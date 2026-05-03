from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from nests.models import Nest, NestMembership

from .models import Comment, Post, PostType


CORE_POST_TYPES = [
    'Question',
    'Discussion',
    'Resource',
    'Announcement',
]


def _require_auth(request: HttpRequest, message: str):
    messages.warning(request, message, 'alert-warning')
    return redirect_to_login(request.get_full_path())


def _ensure_core_post_types():
    items = []
    for name in CORE_POST_TYPES:
        post_type, _ = PostType.objects.get_or_create(name=name)
        items.append(post_type)
    return items


def _group_posts_by_date(posts):
    """Group posts into Today / Yesterday / Older buckets."""
    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)
    groups = {'Today': [], 'Yesterday': [], 'Older': []}
    for post in posts:
        post_date = timezone.localtime(post.created_at).date()
        if post_date == today:
            groups['Today'].append(post)
        elif post_date == yesterday:
            groups['Yesterday'].append(post)
        else:
            groups['Older'].append(post)
    return [(label, items) for label, items in groups.items() if items]


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


def nest_posts_view(request: HttpRequest, nest_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to access nest posts.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _base_nest_context(nest, request.user)
    post_types = _ensure_core_post_types()

    # Nest staff can always post. Members can post too once active.
    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _require_auth(request, 'You must be a nest member to post in this nest.')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        post_type_id = request.POST.get('post_type_id', '')

        selected_post_type = PostType.objects.filter(pk=post_type_id).first()

        if not title or not content or selected_post_type is None:
            messages.error(request, 'Title, content, and post type are required.', 'alert-danger')
        else:
            is_announcement = selected_post_type.name.lower() == 'announcement'
            if is_announcement and not context['is_nest_staff']:
                messages.warning(request, 'Only nest-staff can create announcements.', 'alert-warning')
            else:
                Post.objects.create(
                    user=request.user,
                    nest=nest,
                    title=title,
                    content=content,
                    post_type=selected_post_type,
                )
                messages.success(request, 'Post published successfully.', 'alert-success')
                return redirect('nests:nest_posts', nest_id=nest.pk)

    posts = Post.objects.filter(nest=nest).select_related('user', 'post_type')

    context.update({
        'posts': posts,
        'post_types': post_types,
        'grouped_posts': _group_posts_by_date(posts),
        'active_post': None,
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
        return _require_auth(request, 'You must be a nest member to view posts in this nest.')

    post = get_object_or_404(Post, pk=post_id, nest=nest)
    # Only top-level comments; replies are accessed via comment.replies.all in the template
    top_comments = post.comments.filter(parent=None).prefetch_related('replies__user')

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

    all_posts = Post.objects.filter(nest=nest).select_related('user', 'post_type')
    context.update({
        'post': post,
        'top_comments': top_comments,
        'nest_staff_ids': nest_staff_ids,
        'posts': all_posts,
        'grouped_posts': _group_posts_by_date(all_posts),
        'active_post': post,
    })
    return render(request, 'posts/nest_post_detail.html', context)


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
        return _require_auth(request, 'You must be a nest member to comment.')

    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id', '').strip()

    if not content:
        messages.error(request, 'Comment cannot be empty.', 'alert-danger')
        return redirect('nests:nest_post_detail', nest_id=nest_id, post_id=post_id)

    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post, parent=None)

    Comment.objects.create(
        user=request.user,
        post=post,
        content=content,
        parent=parent,
    )
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
