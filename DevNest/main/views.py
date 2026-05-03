from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login

from .models import ContactMessage, Report
from posts.models import Post, Comment


def home_view(request):
    return render(request, 'main/home.html')


# ── Contact Us ────────────────────────────────────────────────────────────────

def contact_us_view(request: HttpRequest):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        body    = request.POST.get('body', '').strip()
        if not (name and email and subject and body):
            messages.error(request, 'All fields are required.', 'alert-danger')
        else:
            ContactMessage.objects.create(name=name, email=email, subject=subject, body=body)
            messages.success(request, "Your message has been sent. We'll get back to you soon.", 'alert-success')
            return redirect('main:contact_us')
    return render(request, 'main/contact.html')


def staff_messages_view(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, 'Site-staff access only.', 'alert-warning')
        return redirect('accounts:user_profile_view', user_name=request.user.username)

    if request.method == 'POST':
        msg = get_object_or_404(ContactMessage, pk=request.POST.get('message_id'))
        action = request.POST.get('action')
        if action == 'resolve':
            msg.is_resolved = True
            msg.staff_reply = request.POST.get('staff_reply', '').strip()
            msg.resolved_by = request.user
            msg.save()
            messages.success(request, 'Message marked as resolved.', 'alert-success')
        elif action == 'reopen':
            msg.is_resolved = False
            msg.save()
            messages.info(request, 'Message reopened.', 'alert-info')
        return redirect('main:staff_messages')

    open_msgs   = ContactMessage.objects.filter(is_resolved=False)
    closed_msgs = ContactMessage.objects.filter(is_resolved=True)[:20]
    return render(request, 'main/staff_messages.html', {
        'open_msgs': open_msgs,
        'closed_msgs': closed_msgs,
    })


# ── Reports ───────────────────────────────────────────────────────────────────

def report_view(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    post_id    = (request.GET.get('post') or request.POST.get('post_id') or '').strip()
    comment_id = (request.GET.get('comment') or request.POST.get('comment_id') or '').strip()

    post    = get_object_or_404(Post,    pk=post_id)    if post_id    else None
    comment = get_object_or_404(Comment, pk=comment_id) if comment_id else None

    if not post and not comment:
        messages.error(request, 'Nothing to report.', 'alert-danger')
        return redirect('main:home_view')

    if request.method == 'POST':
        reason  = request.POST.get('reason', '').strip()
        details = request.POST.get('details', '').strip()
        if reason not in dict(Report.Reason.choices):
            messages.error(request, 'Please select a reason.', 'alert-danger')
        else:
            already = Report.objects.filter(
                reporter=request.user, post=post, comment=comment, is_resolved=False,
            ).exists()
            if already:
                messages.info(request, 'You have already reported this item.', 'alert-info')
            else:
                Report.objects.create(
                    reporter=request.user, post=post, comment=comment,
                    reason=reason, details=details,
                )
                messages.success(request, 'Report submitted. Thank you.', 'alert-success')
            target_post = post or (comment.post if comment else None)
            if target_post and target_post.nest_id:
                return redirect('nests:nest_post_detail', nest_id=target_post.nest_id, post_id=target_post.pk)
            return redirect('main:home_view')

    return render(request, 'main/report.html', {
        'post': post,
        'comment': comment,
        'reasons': Report.Reason.choices,
    })


def staff_reports_view(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, 'Site-staff access only.', 'alert-warning')
        return redirect('accounts:user_profile_view', user_name=request.user.username)

    if request.method == 'POST':
        report = get_object_or_404(Report, pk=request.POST.get('report_id'))
        action = request.POST.get('action')
        if action == 'resolve':
            report.is_resolved = True
            report.resolved_by = request.user
            report.save()
            messages.success(request, 'Report resolved.', 'alert-success')
        elif action == 'reopen':
            report.is_resolved = False
            report.save()
            messages.info(request, 'Report reopened.', 'alert-info')
        return redirect('main:staff_reports')

    open_reports   = Report.objects.filter(is_resolved=False).select_related('reporter', 'post', 'comment__post')
    closed_reports = Report.objects.filter(is_resolved=True).select_related('reporter', 'post', 'comment__post')[:20]
    return render(request, 'main/staff_reports.html', {
        'open_reports': open_reports,
        'closed_reports': closed_reports,
    })
