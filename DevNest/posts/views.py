from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Count, Q, Sum
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.functions import Coalesce
from email.mime.image import MIMEImage

from main.models import Notification
from nests.models import Nest, NestMembership
from recognition.models import NestRecognition

from .models import Comment, Post, PostReadStatus, PostSubscription, PostTag, PostType, PostVote


CORE_POST_TYPES = [
    'Question',
    'Discussion',
    'Resource',
    'Announcement',
]


def _require_auth(request: HttpRequest, message: str):
    messages.warning(request, message, 'alert-warning')
    return redirect_to_login(request.get_full_path())


def _deny_access(request: HttpRequest, message: str, redirect_to: str, **kwargs):
    """Authenticated but unauthorized — redirect to a safe page with a message."""
    messages.warning(request, message, 'alert-warning')
    return redirect(redirect_to, **kwargs)


def _ensure_core_post_types():
    items = []
    for name in CORE_POST_TYPES:
        post_type, _ = PostType.objects.get_or_create(name=name)
        items.append(post_type)
    return items


def _group_posts_by_date(posts):
    """Group posts: Pinned first (own bucket), then Today / Yesterday / Older."""
    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)
    pinned = []
    date_groups = {'Today': [], 'Yesterday': [], 'Older': []}
    for post in posts:
        if getattr(post, 'is_pinned', False):
            pinned.append(post)
        else:
            post_date = timezone.localtime(post.created_at).date()
            if post_date == today:
                date_groups['Today'].append(post)
            elif post_date == yesterday:
                date_groups['Yesterday'].append(post)
            else:
                date_groups['Older'].append(post)
    result = []
    if pinned:
        result.append(('Pinned', pinned))
    result.extend((label, items) for label, items in date_groups.items() if items)
    return result


def _base_nest_context(nest: Nest, user):
    membership = nest.membership_for(user)
    pending_membership = nest.memberships.filter(
        user=user,
        status=NestMembership.Status.PENDING,
    ).first()
    return {
        'nest': nest,
        'membership': membership,
        'pending_membership': pending_membership,
        'can_manage': nest.is_nest_staff(user) or nest.is_site_staff(user),
        'is_nest_staff': nest.is_nest_staff(user) or nest.is_site_staff(user),
    }


def _normalize_tags(raw_tags: str):
    items = []
    seen = set()
    for chunk in raw_tags.split(','):
        cleaned = ' '.join(chunk.strip().split())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(cleaned[:64])
    return items[:8]


def _resolve_post_tags(raw_tags: str):
    tag_names = _normalize_tags(raw_tags)
    tags = []
    for name in tag_names:
        slug = slugify(name)
        tag = PostTag.objects.filter(slug=slug).first()
        if tag is None:
            tag = PostTag.objects.filter(name__iexact=name).first()
        if tag is None:
            tag = PostTag.objects.create(name=name, slug=slug)
        tags.append(tag)
    return tags


def _serialize_filter_state(request: HttpRequest):
    return {
        'q': request.GET.get('q', '').strip(),
        'type': request.GET.get('type', '').strip(),
        'tag': request.GET.get('tag', '').strip(),
        'sort': request.GET.get('sort', 'newest').strip() or 'newest',
    }


def _apply_post_filters(posts, filter_state):
    q = filter_state['q']
    post_type = filter_state['type']
    tag_slug = filter_state['tag']
    sort = filter_state['sort']

    if q:
        posts = posts.filter(
            Q(title__icontains=q)
            | Q(content__icontains=q)
            | Q(tags__name__icontains=q)
            | Q(user__username__icontains=q)
        )

    if post_type.isdigit():
        posts = posts.filter(post_type_id=int(post_type))

    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    posts = posts.distinct().annotate(
        vote_score=Coalesce(Sum('votes__value'), 0),
        comment_count=Count('comments', distinct=True),
    )

    if sort == 'oldest':
        posts = posts.order_by('-is_pinned', 'created_at')
    elif sort == 'top':
        posts = posts.order_by('-is_pinned', '-vote_score', '-created_at')
    elif sort == 'discussed':
        posts = posts.order_by('-is_pinned', '-comment_count', '-created_at')
    else:
        posts = posts.order_by('-is_pinned', '-created_at')

    return posts


def _attach_user_votes(posts, user):
    if not getattr(user, 'is_authenticated', False):
        return
    vote_map = dict(
        PostVote.objects.filter(user=user, post__in=posts).values_list('post_id', 'value')
    )
    for post in posts:
        post.user_vote = vote_map.get(post.id, 0)


def _recognition_map(nest: Nest) -> dict:
    """Return {user_id: NestRecognition} for every recognised user in the nest."""
    return {
        r.user_id: r
        for r in NestRecognition.objects.filter(nest=nest).only(
            'user_id', 'title', 'badge'
        )
    }


def _attach_recognition(items, rec_map: dict, user_attr: str = 'user'):
    """Attach `.recognition` to each item based on the item's user FK."""
    for item in items:
        user_id = getattr(getattr(item, user_attr), 'pk', None)
        item.recognition = rec_map.get(user_id)


def _attach_subscription_state(posts, user):
    if not posts or not getattr(user, 'is_authenticated', False):
        return

    post_ids = [post.pk for post in posts]
    rows = PostSubscription.objects.filter(post_id__in=post_ids, user=user).values_list('post_id', 'is_enabled')
    subscription_map = {post_id: is_enabled for post_id, is_enabled in rows}

    for post in posts:
        if post.pk in subscription_map:
            post.is_subscribed = subscription_map[post.pk]
        else:
            # Keep "author default on" behavior for old posts without an explicit record yet.
            post.is_subscribed = post.user_id == user.pk


def _attach_read_state(posts, user, active_post_id=None):
    if not posts or not getattr(user, 'is_authenticated', False):
        return

    post_ids = [post.pk for post in posts]
    read_post_ids = set(
        PostReadStatus.objects.filter(post_id__in=post_ids, user=user).values_list('post_id', flat=True)
    )

    for post in posts:
        is_read = post.pk in read_post_ids or post.user_id == user.pk
        if active_post_id and post.pk == active_post_id:
            is_read = True
        post.is_read = is_read


def _upsert_post_subscription(post: Post, user, is_enabled: bool):
    subscription, created = PostSubscription.objects.get_or_create(
        post=post,
        user=user,
        defaults={'is_enabled': is_enabled},
    )
    if not created and subscription.is_enabled != is_enabled:
        subscription.is_enabled = is_enabled
        subscription.save(update_fields=['is_enabled', 'updated_at'])


def _attach_email_logo(email_message, logo_cid='devnest-logo'):
    logo_path = settings.BASE_DIR / 'main' / 'static' / 'images' / 'logo.svg'
    try:
        with open(logo_path, 'rb') as logo_file:
            logo = MIMEImage(logo_file.read(), _subtype='svg+xml')
        logo.add_header('Content-ID', f'<{logo_cid}>')
        logo.add_header('Content-Disposition', 'inline', filename='logo.svg')
        email_message.attach(logo)
    except OSError:
        # Keep email delivery working even if logo file is missing.
        pass


def _send_post_update_emails(post: Post, actor, comment: Comment):
    post_path = reverse('nests:nest_post_detail', kwargs={'nest_id': post.nest_id, 'post_id': post.pk})
    post_url = f"{settings.SITE_URL.rstrip('/')}{post_path}"
    is_reply = comment.parent_id is not None
    event_label = 'reply' if is_reply else 'comment'
    actor_name = actor.get_full_name() or actor.username
    subscriptions = PostSubscription.objects.filter(post=post, is_enabled=True).select_related('user')

    for subscription in subscriptions:
        recipient = subscription.user
        if recipient.pk == actor.pk:
            continue

        Notification.objects.create(
            user=recipient,
            message=f'{actor_name} added a new {event_label} on "{post.title}".',
            link=post_path,
        )

        if not recipient.email:
            continue

        context = {
            'recipient_name': recipient.get_full_name() or recipient.username,
            'actor_name': actor_name,
            'post_title': post.title,
            'nest_name': post.nest.name if post.nest_id else 'DevNest',
            'event_label': event_label,
            'comment_content': comment.content,
            'post_url': post_url,
            'site_url': settings.SITE_URL,
            'logo_cid': 'devnest-logo',
        }
        html_content = render_to_string('posts/emails/post_update.html', context)
        email_message = EmailMessage(
            f"New {event_label} on: {post.title}",
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
        )
        email_message.content_subtype = 'html'
        _attach_email_logo(email_message, logo_cid='devnest-logo')
        email_message.send(fail_silently=True)


def _send_announcement_emails(post: Post, actor):
    if not post.nest_id:
        return

    post_path = reverse('nests:nest_post_detail', kwargs={'nest_id': post.nest_id, 'post_id': post.pk})
    post_url = f"{settings.SITE_URL.rstrip('/')}{post_path}"
    actor_name = actor.get_full_name() or actor.username

    memberships = post.nest.memberships.filter(
        status=NestMembership.Status.ACTIVE,
    ).select_related('user')

    for membership in memberships:
        recipient = membership.user
        if recipient.pk == actor.pk:
            continue

        Notification.objects.create(
            user=recipient,
            message=f'New announcement in {post.nest.name}: "{post.title}"',
            link=post_path,
        )

        if not recipient.email:
            continue
        context = {
            'recipient_name': recipient.get_full_name() or recipient.username,
            'actor_name': actor_name,
            'nest_name': post.nest.name,
            'post_title': post.title,
            'post_content': post.content,
            'post_url': post_url,
            'site_url': settings.SITE_URL,
            'logo_cid': 'devnest-logo',
        }
        html_content = render_to_string('posts/emails/announcement.html', context)
        email_message = EmailMessage(
            f"New announcement in {post.nest.name}: {post.title}",
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
        )
        email_message.content_subtype = 'html'
        _attach_email_logo(email_message, logo_cid='devnest-logo')
        email_message.send(fail_silently=True)


def nest_posts_view(request: HttpRequest, nest_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to access nest posts.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _base_nest_context(nest, request.user)
    all_post_types = _ensure_core_post_types()
    if context['is_nest_staff']:
        post_types = all_post_types
    else:
        post_types = [p for p in all_post_types if p.name.lower() != 'announcement']

    # Nest staff can always post. Members can post too once active.
    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to access posts.', 'nests:nest_detail', nest_id=nest.pk)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        post_type_id = request.POST.get('post_type_id', '')
        raw_tags = request.POST.get('tags', '').strip()
        subscribe_updates = request.POST.get('subscribe_updates') == '1'

        selected_post_type = PostType.objects.filter(pk=post_type_id).first()

        if not title or not content or selected_post_type is None:
            messages.error(request, 'Title, content, and post type are required.', 'alert-danger')
        else:
            is_announcement = selected_post_type.name.lower() == 'announcement'
            if is_announcement and not context['is_nest_staff']:
                messages.warning(request, 'Only nest-staff can create announcements.', 'alert-warning')
            else:
                post = Post.objects.create(
                    user=request.user,
                    nest=nest,
                    title=title,
                    content=content,
                    post_type=selected_post_type,
                )
                tags = _resolve_post_tags(raw_tags)
                if tags:
                    post.tags.set(tags)
                _upsert_post_subscription(post, request.user, is_enabled=subscribe_updates)
                if is_announcement and context['is_nest_staff']:
                    try:
                        _send_announcement_emails(post, request.user)
                    except Exception as e:
                        print(f'Announcement email failed: {e}')
                messages.success(request, 'Post published successfully.', 'alert-success')
                return redirect('nests:nest_posts', nest_id=nest.pk)

    filter_state = _serialize_filter_state(request)
    base_posts = Post.objects.filter(nest=nest).select_related('user', 'post_type').prefetch_related('tags')
    posts = list(_apply_post_filters(base_posts, filter_state))
    _attach_user_votes(posts, request.user)
    _attach_subscription_state(posts, request.user)
    _attach_read_state(posts, request.user)
    rec_map = _recognition_map(nest)
    _attach_recognition(posts, rec_map)
    available_tags = PostTag.objects.filter(posts__nest=nest).distinct().order_by('name')

    active_filters_count = sum(
        1 for key in ('q', 'type', 'tag') if filter_state[key]
    ) + (1 if filter_state['sort'] != 'newest' else 0)

    context.update({
        'posts': posts,
        'post_types': post_types,
        'grouped_posts': _group_posts_by_date(posts),
        'active_post': None,
        'available_tags': available_tags,
        'filter_state': filter_state,
        'active_filters_count': active_filters_count,
        'current_query': request.GET.urlencode(),
    })
    return render(request, 'posts/nest_posts.html', context)


def nest_post_detail_view(request: HttpRequest, nest_id: int, post_id: int):
    """Full post view with threaded comments and comment form."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view this post.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _base_nest_context(nest, request.user)

    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to view posts.', 'nests:nest_detail', nest_id=nest.pk)

    post = get_object_or_404(
        Post.objects.select_related('user', 'post_type').prefetch_related('tags'),
        pk=post_id,
        nest=nest,
    )
    # Only top-level comments; replies are accessed via comment.replies.all in the template
    top_comments = post.comments.filter(parent=None).select_related('user').prefetch_related('replies__user')

    # Build the set of user PKs who are nest-staff (instructor/assistant) or site-staff
    staff_pks = set(
        nest.memberships.filter(
            status=NestMembership.Status.ACTIVE,
            role__in=[NestMembership.Role.INSTRUCTOR, NestMembership.Role.ASSISTANT],
        ).values_list('user_id', flat=True)
    )
    User = get_user_model()
    site_staff_pks = set(
        User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).values_list('pk', flat=True)
    )
    nest_staff_ids = staff_pks | site_staff_pks

    filter_state = _serialize_filter_state(request)
    all_posts_qs = Post.objects.filter(nest=nest).select_related('user', 'post_type').prefetch_related('tags')
    all_posts = list(_apply_post_filters(all_posts_qs, filter_state))
    _attach_user_votes(all_posts, request.user)
    _attach_subscription_state(all_posts, request.user)
    _attach_read_state(all_posts, request.user, active_post_id=post.pk)
    rec_map = _recognition_map(nest)
    _attach_recognition(all_posts, rec_map)

    PostReadStatus.objects.update_or_create(post=post, user=request.user)
    post_vote = PostVote.objects.filter(post=post, user=request.user).values_list('value', flat=True).first()
    subscription, _ = PostSubscription.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'is_enabled': request.user.pk == post.user_id},
    )
    post.vote_score = PostVote.objects.filter(post=post).aggregate(total=Coalesce(Sum('value'), 0))['total']
    post.user_vote = post_vote or 0
    post.recognition = rec_map.get(post.user_id)

    # Attach recognition to comments and their replies
    top_comments_list = list(top_comments)
    _attach_recognition(top_comments_list, rec_map)
    for comment in top_comments_list:
        _attach_recognition(list(comment.replies.all()), rec_map)

    available_tags = PostTag.objects.filter(posts__nest=nest).distinct().order_by('name')
    active_filters_count = sum(
        1 for key in ('q', 'type', 'tag') if filter_state[key]
    ) + (1 if filter_state['sort'] != 'newest' else 0)

    context.update({
        'post': post,
        'top_comments': top_comments_list,
        'nest_staff_ids': nest_staff_ids,
        'posts': all_posts,
        'grouped_posts': _group_posts_by_date(all_posts),
        'active_post': post,
        'post_types': _ensure_core_post_types(),
        'available_tags': available_tags,
        'filter_state': filter_state,
        'active_filters_count': active_filters_count,
        'current_query': request.GET.urlencode(),
        'is_subscribed_to_post': subscription.is_enabled,
    })
    return render(request, 'posts/nest_post_detail.html', context)


def toggle_post_subscription_view(request: HttpRequest, nest_id: int, post_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to manage post updates.')

    if request.method != 'POST':
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    post = get_object_or_404(Post, pk=post_id, nest=nest)

    membership = nest.membership_for(request.user)
    is_staff = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    if not (is_staff or membership is not None):
        return _deny_access(request, 'You must be an active nest member to manage updates.', 'nests:nest_detail', nest_id=nest_id)

    wants_subscription = request.POST.get('subscribe') == '1'
    _upsert_post_subscription(post, request.user, is_enabled=wants_subscription)
    if wants_subscription:
        messages.success(request, 'Email updates enabled for this post.', 'alert-success')
    else:
        messages.info(request, 'Email updates turned off for this post.', 'alert-info')

    return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)


def vote_post_view(request: HttpRequest, nest_id: int, post_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to vote.')

    if request.method != 'POST':
        return redirect('nests:nest_posts', nest_id=nest_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    membership = nest.membership_for(request.user)
    is_staff = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    if not (is_staff or membership is not None):
        return _deny_access(request, 'You must be an active nest member to vote.', 'nests:nest_detail', nest_id=nest_id)

    post = get_object_or_404(Post, pk=post_id, nest=nest)

    raw_value = request.POST.get('value', '').strip()
    if raw_value not in {'1', '-1'}:
        messages.error(request, 'Invalid vote request.', 'alert-danger')
    else:
        value = int(raw_value)
        vote = PostVote.objects.filter(post=post, user=request.user).first()
        if vote and vote.value == value:
            vote.delete()
            messages.info(request, 'Your vote was removed.', 'alert-info')
        elif vote:
            vote.value = value
            vote.save(update_fields=['value', 'updated_at'])
            messages.success(request, 'Your vote was updated.', 'alert-success')
        else:
            PostVote.objects.create(post=post, user=request.user, value=value)
            messages.success(request, 'Thanks for voting.', 'alert-success')

    next_url = request.POST.get('next', '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('nests:nest_posts', nest_id=nest_id)


def add_comment_view(request: HttpRequest, nest_id: int, post_id: int):
    """POST only. Add a top-level comment or a reply to a comment."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to comment.')

    if request.method != 'POST':
        return redirect('nests:nest_posts', nest_id=nest_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    post = get_object_or_404(Post, pk=post_id, nest=nest)

    membership = nest.membership_for(request.user)
    is_staff = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    if not (is_staff or membership is not None):
        return _deny_access(request, 'You must be an active nest member to comment.', 'nests:nest_detail', nest_id=nest_id)

    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id', '').strip()

    if not content:
        messages.error(request, 'Comment cannot be empty.', 'alert-danger')
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post, parent=None)

    new_comment = Comment.objects.create(
        user=request.user,
        post=post,
        content=content,
        parent=parent,
    )
    try:
        _send_post_update_emails(post, request.user, new_comment)
    except Exception as e:
        print(f'Post update email failed: {e}')
    messages.success(request, 'Comment posted.', 'alert-success')
    return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)


def verify_comment_view(request: HttpRequest, nest_id: int, post_id: int, comment_id: int):
    """POST only. Nest-staff marks a member comment as a verified answer."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in.')

    if request.method != 'POST':
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not (nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)):
        messages.warning(request, 'Only nest-staff can verify answers.', 'alert-warning')
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    post = get_object_or_404(Post, pk=post_id, nest=nest)
    comment = get_object_or_404(Comment, pk=comment_id, post=post, parent=None)

    comment.is_verified = not comment.is_verified
    comment.save(update_fields=['is_verified'])
    action = 'marked as verified' if comment.is_verified else 'unmarked'
    messages.success(request, f'Answer {action}.', 'alert-success')
    return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)


def delete_post_view(request: HttpRequest, nest_id: int, post_id: int):
    """POST only. Nest-staff or post author can delete a post."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in.')
    if request.method != 'POST':
        return redirect('nests:nest_posts', nest_id=nest_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    post = get_object_or_404(Post, pk=post_id, nest=nest)

    is_staff = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    is_author = post.user == request.user
    if not (is_staff or is_author):
        return _deny_access(request, 'You do not have permission to delete this post.', 'nests:nest_posts', nest_id=nest_id)

    post.delete()
    messages.success(request, 'Post deleted.', 'alert-success')
    return redirect('nests:nest_posts', nest_id=nest_id)


def delete_comment_view(request: HttpRequest, nest_id: int, post_id: int, comment_id: int):
    """POST only. Nest-staff or comment author can delete a comment."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in.')
    if request.method != 'POST':
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    post = get_object_or_404(Post, pk=post_id, nest=nest)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    is_staff = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    is_author = comment.user == request.user
    if not (is_staff or is_author):
        return _deny_access(request, 'You do not have permission to delete this comment.', 'nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    comment.delete()
    messages.success(request, 'Comment deleted.', 'alert-success')
    return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)


def pin_post_view(request: HttpRequest, nest_id: int, post_id: int):
    """POST only. Nest-staff can toggle pin on a post."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in.')
    if request.method != 'POST':
        return redirect('nests:nest_posts', nest_id=nest_id)

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not (nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)):
        return _deny_access(request, 'Only nest-staff can pin posts.', 'nests:nest_posts', nest_id=nest_id)

    post = get_object_or_404(Post, pk=post_id, nest=nest)
    post.is_pinned = not post.is_pinned
    post.save(update_fields=['is_pinned'])
    action = 'pinned' if post.is_pinned else 'unpinned'
    messages.success(request, f'Post {action}.', 'alert-success')

    next_url = request.POST.get('next', '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('nests:nest_posts', nest_id=nest_id)
