from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import Sum 
from assessments.models import  Submission

from posts.models import Post, PostType

from .models import Nest, NestMembership


def _require_auth(request, message):
    """Flash a message and redirect to the sign-in page, preserving the next URL."""
    messages.warning(request, message, 'alert-warning')
    return redirect_to_login(request.get_full_path())


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

    return render(request, 'nests/dashboard.html', {
        'nests': my_nests,
        'pending_nests': pending_nests,
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
    # Attach the user's membership status to each nest for the template
    user_nest_ids = set(
        NestMembership.objects.filter(user=request.user)
        .values_list('nest_id', flat=True)
    )
    return render(request, 'nests/nest_list.html', {
        'nests': nests,
        'user_nest_ids': user_nest_ids,
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
    recent_posts = (
        Post.objects.filter(nest=nest)
        .exclude(post_type=ann_type)
        .order_by('-created_at')[:5]
        if ann_type else Post.objects.filter(nest=nest).order_by('-created_at')[:5]
    )

    return render(request, 'nests/nest_detail.html', {
        'nest': nest,
        'membership': membership,
        'pending_membership': pending_membership,
        'can_manage': nest.is_nest_staff(request.user) or nest.is_site_staff(request.user),
        'announcements': announcements,
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
        return redirect('nests:nest_detail', nest_id=nest.pk)

    NestMembership.objects.create(
        nest=nest,
        user=request.user,
        role=NestMembership.Role.MEMBER,
        status=NestMembership.Status.PENDING,
    )
    messages.success(request, f'Your request to join "{nest.name}" has been sent to the instructor.', 'alert-success')
    return redirect('nests:nest_detail', nest_id=nest.pk)


def manage_nest_view(request: HttpRequest, nest_id: int):
    """Nest management page — only for nest staff (instructor / assistant).
    Lists pending join requests; instructor can approve or reject each one.
    """
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in and be a nest-staff member to manage a nest.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)

    if not (nest.is_nest_staff(request.user) or nest.is_site_staff(request.user)):
        return _require_auth(request, 'You must be a nest-staff member (instructor or assistant) to manage this nest.')

    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        action        = request.POST.get('action')  # 'approve' or 'reject'

        membership = get_object_or_404(NestMembership, pk=membership_id, nest=nest)
        if action == 'approve':
            membership.status = NestMembership.Status.ACTIVE
            membership.save()
            messages.success(request, f'{membership.user.username} has been approved.', 'alert-success')
        elif action == 'reject':
            membership.status = NestMembership.Status.REJECTED
            membership.save()
            messages.warning(request, f'{membership.user.username} has been rejected.', 'alert-warning')

        return redirect('nests:manage_nest', nest_id=nest.pk)

    pending_requests = nest.memberships.filter(status=NestMembership.Status.PENDING)
    active_members   = nest.memberships.filter(status=NestMembership.Status.ACTIVE)
    return render(request, 'nests/manage_nest.html', {
        'nest': nest,
        'pending_requests': pending_requests,
        'active_members': active_members,
    })


def staff_nest_review_view(request: HttpRequest):
    """Site-staff only. Lists all pending nest requests and lets staff approve or reject them."""
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in and be a site-staff member to access the review panel.')

    if not (request.user.is_staff or request.user.is_superuser):
        return _require_auth(request, 'You must be a site-staff member to access the nest review panel.')

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
