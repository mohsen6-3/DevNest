from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import datetime
from assessments.models import Assessment, Submission

from posts.models import Post, PostType, PostVote, Comment

from .models import Nest, NestMembership


def _require_auth(request, message):
    """Flash a message and redirect to the sign-in page, preserving the next URL."""
    messages.warning(request, message, 'alert-warning')
    return redirect_to_login(request.get_full_path())


def _deny_access(request, message, redirect_to='nests:nest_dashboard', **redirect_kwargs):
    """Authenticated user lacks permission — redirect to a safe page with a message."""
    messages.warning(request, message, 'alert-warning')
    return redirect(redirect_to, **redirect_kwargs)


def nest_dashboard(request):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view your dashboard.')
    # Nests the user is an active member of (approved nests only)
    my_nests = Nest.objects.filter(
        status=Nest.Status.APPROVED,
        memberships__user=request.user,
        memberships__status=NestMembership.Status.ACTIVE,
    ).distinct()

    # Nests the user requested that are still waiting for site-staff approval
    pending_nests = Nest.objects.filter(
        creator=request.user,
        status=Nest.Status.PENDING,
    )

    # ── Extra context for dashboard enhancements ───────────────────────────
    now = timezone.now()
    week_ago = now - datetime.timedelta(days=7)
    my_nest_ids = list(my_nests.values_list('pk', flat=True))

    # #8 Weekly stats
    if my_nest_ids:
        posts_this_week = Post.objects.filter(
            nest_id__in=my_nest_ids, created_at__gte=week_ago
        ).count()
        comments_this_week = Comment.objects.filter(
            post__nest_id__in=my_nest_ids, created_at__gte=week_ago
        ).count()

        # #7 Needs Attention – unanswered posts (posts with 0 comments) in user's nests
        unanswered_posts = Post.objects.filter(
            nest_id__in=my_nest_ids
        ).annotate(num_comments=Count('comments')).filter(num_comments=0).order_by('-created_at')[:5]

        # #1 Smart alerts – upcoming assessments due in the next 7 days not yet submitted
        upcoming_assessments = Assessment.objects.filter(
            nest_id__in=my_nest_ids,
            due_date__isnull=False,
            due_date__gte=now,
            due_date__lte=now + datetime.timedelta(days=7),
        ).exclude(
            submissions__student=request.user
        ).distinct().order_by('due_date')[:5]
    else:
        posts_this_week = 0
        comments_this_week = 0
        unanswered_posts = Post.objects.none()
        upcoming_assessments = Assessment.objects.none()

    # #10 Role-based – nest staff: pending membership requests in nests I manage
    managed_nest_ids = list(
        NestMembership.objects.filter(
            user=request.user,
            status=NestMembership.Status.ACTIVE,
            role__in=[NestMembership.Role.INSTRUCTOR, NestMembership.Role.ASSISTANT],
        ).values_list('nest_id', flat=True)
    )
    pending_memberships = NestMembership.objects.filter(
        nest_id__in=managed_nest_ids,
        status=NestMembership.Status.PENDING,
    ).select_related('user', 'nest')[:10]

    # #10 Role-based – site staff: pending nest requests
    pending_nest_requests = Nest.objects.filter(status=Nest.Status.PENDING) if (
        request.user.is_staff or request.user.is_superuser
    ) else Nest.objects.none()

    is_site_staff = request.user.is_staff or request.user.is_superuser
    is_nest_staff = len(managed_nest_ids) > 0
    managed_nests = my_nests.filter(pk__in=managed_nest_ids)
    # ───────────────────────────────────────────────────────────────────────

    return render(request, 'nests/dashboard.html', {
        'nests': my_nests,
        'pending_nests': pending_nests,
        # extras
        'posts_this_week': posts_this_week,
        'comments_this_week': comments_this_week,
        'unanswered_posts': unanswered_posts,
        'upcoming_assessments': upcoming_assessments,
        'pending_memberships': pending_memberships,
        'pending_nest_requests': pending_nest_requests,
        'is_site_staff': is_site_staff,
        'is_nest_staff': is_nest_staff,
        'managed_nests': managed_nests,
    })


def request_nest_view(request: HttpRequest):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to request a nest.')
    """Any logged-in user can request a new nest.
    It starts as PENDING until site staff approves it.
    The requester becomes the instructor automatically.
    """
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not description:
            messages.error(request, 'Name and description are required.', 'alert-danger')
            return render(request, 'nests/request_nest.html')

        nest = Nest.objects.create(
            name=name,
            description=description,
            creator=request.user,
            status=Nest.Status.PENDING,
        )
        NestMembership.objects.create(
            nest=nest,
            user=request.user,
            role=NestMembership.Role.INSTRUCTOR,
            status=NestMembership.Status.ACTIVE,
        )
        messages.success(request, f'"{nest.name}" has been submitted for review. You will be notified once it is approved.', 'alert-success')
        return redirect('nests:nest_dashboard')

    return render(request, 'nests/request_nest.html')


def nest_list_view(request: HttpRequest):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to browse nests.')
    """Browse all approved nests."""
    nests = Nest.objects.filter(status=Nest.Status.APPROVED).order_by('name')
    # Attach active/pending membership status so the browse cards render correctly.
    memberships = NestMembership.objects.filter(user=request.user).values_list('nest_id', 'status')
    active_nest_ids = {nest_id for nest_id, status in memberships if status == NestMembership.Status.ACTIVE}
    pending_nest_ids = {nest_id for nest_id, status in memberships if status == NestMembership.Status.PENDING}

    return render(request, 'nests/nest_list.html', {
        'nests': nests,
        'active_nest_ids': active_nest_ids,
        'pending_nest_ids': pending_nest_ids,
        'is_site_staff': request.user.is_staff or request.user.is_superuser,
    })


def nest_detail_view(request: HttpRequest, nest_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view nest details.')
    """Dashboard for an approved nest: shows announcements and recent posts."""
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    membership = nest.membership_for(request.user)
    pending_membership = nest.memberships.filter(
        user=request.user, status=NestMembership.Status.PENDING
    ).first()
    can_manage = nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)
    has_access = can_manage or (membership is not None)
    if not has_access:
        if pending_membership:
            return _deny_access(
                request,
                'Your join request is still pending. You can view this nest after approval.',
                'nests:nest_list_view',
            )
        return _deny_access(
            request,
            'You must be an active nest member to view this nest.',
            'nests:nest_list_view',
        )

    total_score = (
        Submission.objects
        .filter(student=request.user, assessment__nest=nest)
        .aggregate(total=Sum('score'))['total'] or 0
    )

    ann_type = PostType.objects.filter(name='Announcement').first()
    announcements = (
        Post.objects.filter(nest=nest, post_type=ann_type).order_by('-created_at')[:5]
        if ann_type else []
    )
    pinned_posts = (
        Post.objects.filter(nest=nest, is_pinned=True)
        .exclude(post_type=ann_type)
        .order_by('-created_at')[:5]
        if ann_type else Post.objects.filter(nest=nest, is_pinned=True).order_by('-created_at')[:5]
    )
    recent_posts = (
        Post.objects.filter(nest=nest)
        .exclude(is_pinned=True)
        .exclude(post_type=ann_type)
        .order_by('-created_at')[:5]
        if ann_type else Post.objects.filter(nest=nest).exclude(is_pinned=True).order_by('-created_at')[:5]
    )

    return render(request, 'nests/nest_detail.html', {
        'nest': nest,
        'membership': membership,
        'pending_membership': pending_membership,
        'can_manage': can_manage,
        'announcements': announcements,
        'pinned_posts': pinned_posts,
        'recent_posts': recent_posts,
        'total_score': total_score,
    })


def join_nest_view(request: HttpRequest, nest_id: int):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to join a nest.')
    """POST only. Student requests to join a nest. Creates a PENDING membership."""
    if request.method != 'POST':
        return redirect('nests:nest_dashboard')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)

    # Already a member or already requested — ignore
    if nest.memberships.filter(user=request.user).exists():
        messages.info(request, 'You already have a membership or pending request for this nest.', 'alert-info')
        return redirect('nests:nest_list_view')

    NestMembership.objects.create(
        nest=nest,
        user=request.user,
        role=NestMembership.Role.MEMBER,
        status=NestMembership.Status.PENDING,
    )
    messages.success(request, f'Your request to join "{nest.name}" has been sent to the instructor.', 'alert-success')
    return redirect('nests:nest_list_view')


def manage_nest_view(request: HttpRequest, nest_id: int):
    """Nest management page — only for nest staff (instructor / assistant).
    Lists pending join requests; instructor can approve or reject each one.
    """
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in and be a nest-staff member to manage a nest.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)

    if not (nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)):
        return _deny_access(request, 'Only nest-staff (instructor or assistant) can manage this nest.', 'nests:nest_detail', nest_id=nest.pk)

    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        action        = request.POST.get('action')  # 'approve', 'reject', 'promote'

        membership = get_object_or_404(NestMembership, pk=membership_id, nest=nest)
        if action == 'approve':
            membership.status = NestMembership.Status.ACTIVE
            membership.save()
            messages.success(request, f'{membership.user.username} has been approved.', 'alert-success')
        elif action == 'reject':
            membership.status = NestMembership.Status.REJECTED
            membership.save()
            messages.warning(request, f'{membership.user.username} has been rejected.', 'alert-warning')
        elif action == 'promote':
            if membership.role == NestMembership.Role.MEMBER and membership.status == NestMembership.Status.ACTIVE:
                membership.role = NestMembership.Role.ASSISTANT
                membership.save()
                messages.success(request, f'{membership.user.username} has been promoted to Assistant.', 'alert-success')
        elif action == 'demote':
            if membership.role == NestMembership.Role.ASSISTANT and membership.status == NestMembership.Status.ACTIVE:
                membership.role = NestMembership.Role.MEMBER
                membership.save()
                messages.success(request, f'{membership.user.username} has been demoted to Member.', 'alert-success')

        return redirect('nests:manage_nest', nest_id=nest.pk)

    pending_requests = nest.memberships.filter(status=NestMembership.Status.PENDING)
    active_members   = nest.memberships.filter(status=NestMembership.Status.ACTIVE).select_related('user')

    # Engagement analytics: post count, comment count, upvotes received per member
    from recognition.models import NestRecognition
    rec_map = {r.user_id: r for r in NestRecognition.objects.filter(nest=nest)}
    analytics = []
    for m in active_members:
        post_count    = Post.objects.filter(user=m.user, nest=nest).count()
        comment_count = Comment.objects.filter(user=m.user, post__nest=nest).count()
        vote_score    = (
            PostVote.objects.filter(post__nest=nest, post__user=m.user)
            .aggregate(total=Coalesce(Sum('value'), Value(0)))['total']
        )
        rec = rec_map.get(m.user_id)
        analytics.append({
            'membership': m,
            'post_count': post_count,
            'comment_count': comment_count,
            'vote_score': vote_score,
            'rec': rec,
        })

    return render(request, 'nests/manage_nest.html', {
        'nest': nest,
        'pending_requests': pending_requests,
        'active_members': active_members,
        'analytics': analytics,
    })


def staff_nest_review_view(request: HttpRequest):
    """Site-staff only. Lists all pending nest requests and lets staff approve or reject them."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to access the review panel.')

    if not (request.user.is_staff or request.user.is_superuser):
        return _deny_access(request, 'Only site-staff can access the nest review panel.')

    if request.method == 'POST':
        nest_id = request.POST.get('nest_id')
        action  = request.POST.get('action')  # 'approve' or 'reject'

        nest = get_object_or_404(Nest, pk=nest_id)
        if action == 'approve':
            nest.status = Nest.Status.APPROVED
            nest.save()
            messages.success(request, f'"{nest.name}" has been approved.', 'alert-success')
        elif action == 'reject':
            nest.status = Nest.Status.REJECTED
            nest.save()
            messages.warning(request, f'"{nest.name}" has been rejected.', 'alert-warning')

        return redirect('nests:staff_nest_review')

    pending  = Nest.objects.filter(status=Nest.Status.PENDING).order_by('name')
    approved = Nest.objects.filter(status=Nest.Status.APPROVED).order_by('name')
    rejected = Nest.objects.filter(status=Nest.Status.REJECTED).order_by('name')
    return render(request, 'nests/staff_nest_review.html', {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
    })


def create_nest_view(request: HttpRequest):
    """Site-staff only: create an already-approved nest and assign roles directly."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in.')
    if not (request.user.is_staff or request.user.is_superuser):
        return _deny_access(request, 'Only site-staff can create nests directly.')

    User = get_user_model()
    users = User.objects.order_by('username')

    if request.method == 'POST':
        name          = request.POST.get('name', '').strip()
        description   = request.POST.get('description', '').strip()
        instructor_id = request.POST.get('instructor', '').strip()
        assistant_ids = set(request.POST.getlist('assistants'))
        member_ids    = set(request.POST.getlist('members'))

        if not name or not description or not instructor_id:
            messages.error(request, 'Name, description, and instructor are required.', 'alert-danger')
        else:
            try:
                with transaction.atomic():
                    instructor = get_object_or_404(User, pk=instructor_id)
                    nest = Nest.objects.create(
                        name=name, description=description,
                        creator=instructor, status=Nest.Status.APPROVED,
                    )
                    NestMembership.objects.create(
                        nest=nest, user=instructor,
                        role=NestMembership.Role.INSTRUCTOR,
                        status=NestMembership.Status.ACTIVE,
                    )
                    for uid in assistant_ids - {instructor_id}:
                        u = User.objects.filter(pk=uid).first()
                        if u:
                            NestMembership.objects.get_or_create(
                                nest=nest, user=u,
                                defaults={'role': NestMembership.Role.ASSISTANT, 'status': NestMembership.Status.ACTIVE},
                            )
                    for uid in member_ids - {instructor_id} - assistant_ids:
                        u = User.objects.filter(pk=uid).first()
                        if u:
                            NestMembership.objects.get_or_create(
                                nest=nest, user=u,
                                defaults={'role': NestMembership.Role.MEMBER, 'status': NestMembership.Status.ACTIVE},
                            )
                messages.success(request, f'Nest "{nest.name}" created successfully.', 'alert-success')
                return redirect('nests:nest_detail', nest_id=nest.pk)
            except Exception as e:
                messages.error(request, 'Could not create nest. Please try again.', 'alert-danger')
                print(e)

    return render(request, 'nests/create_nest.html', {'users': users})
