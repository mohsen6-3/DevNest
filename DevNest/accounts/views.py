from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import redirect_to_login
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.image import MIMEImage
from .models import Profile
from django.db import transaction
from posts.models import Post
from posts.models import Comment
from nests.models import NestMembership
from recognition.models import NestRecognition
from main.models import ContactMessage, Report



# Create your views here.


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


def send_welcome_email(user):
    """Send welcome email to newly registered user."""
    context = {
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'site_url': settings.SITE_URL,
        'logo_cid': 'devnest-logo',
    }
    content_html = render_to_string('accounts/emails/welcome.html', context)
    email_message = EmailMessage(
        'Welcome to DevNest!',
        content_html,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email_message.content_subtype = 'html'
    _attach_email_logo(email_message, logo_cid='devnest-logo')
    email_message.send(fail_silently=True)


def sign_up(request: HttpRequest):

    if request.method == "POST":

        try:
            with transaction.atomic():
                new_user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password"],
                    email=request.POST["email"],
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"],
                )

                profile = new_user.profile
                profile.about = request.POST.get("about", "")
                profile.social_link = request.POST.get("social_link", "")
                uploaded_avatar = request.FILES.get("avatar")
                if uploaded_avatar:
                    profile.avatar = uploaded_avatar
                profile.save()
        except Exception as e:
            messages.error(request, "Couldn't register user. Try again", "alert-danger")
            print(e)

        else:
            try:
                send_welcome_email(new_user)
            except Exception as e:
                print(e)
                messages.warning(request, "Account created, but welcome email could not be sent.", "alert-warning")

            messages.success(request, "Registered User Successfuly", "alert-success")
            login(request, new_user)
            return redirect("nests:nest_dashboard")
    
    return render(request, "accounts/signup.html", {})


@never_cache
def sign_in(request:HttpRequest):

    if request.method == "POST":

        #checking user credentials
        user = authenticate(request, username=request.POST["username"], password=request.POST["password"])
        print(user)
        if user:
            #login the user
            login(request, user)
            messages.success(request, "Logged in successfully", "alert-success")
            return redirect("nests:nest_dashboard")
        else:
            print("user not found")
            messages.error(request, "Please try again. You credentials are wrong", "alert-danger")



    return render(request, "accounts/signin.html")


def log_out(request: HttpRequest):

    logout(request)
    messages.success(request, "logged out successfully", "alert-warning")

    next_url = request.GET.get('next', '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("accounts:sign_in")

def user_profile_view(request: HttpRequest, user_name):
    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        messages.warning(request, f'No user found with username "{user_name}".', 'alert-warning')
        return redirect('main:home_view')

    # Nests the user is an active member of
    active_memberships = NestMembership.objects.filter(
        user=user, status=NestMembership.Status.ACTIVE
    ).select_related('nest')
    nests = [m.nest for m in active_memberships]

    # Recognition per nest (build a {nest_id: recognition} lookup)
    nest_ids = [n.pk for n in nests]
    recognitions_qs = NestRecognition.objects.filter(user=user, nest_id__in=nest_ids)
    recognition_map = {r.nest_id: r for r in recognitions_qs}
    # Attach recognition to each nest for easy template access
    nests_with_recognition = [
        (nest, recognition_map.get(nest.pk)) for nest in nests
    ]

    # Posts authored by the user
    posts = Post.objects.filter(user=user).order_by('-created_at')
    profile_comment_count = Comment.objects.filter(user=user).count()

    post_count_value = posts.count()
    if post_count_value >= 40 and profile_comment_count >= 40:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('Community Leader', 'chief', 'bi-stars')
    elif post_count_value >= 20 and profile_comment_count >= 20:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('Highly Engaged', 'fire', 'bi-lightning-charge-fill')
    elif post_count_value >= 10 and profile_comment_count >= 10:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('Engaged', 'engaged', 'bi-fire')
    elif post_count_value >= 5 and profile_comment_count >= 5:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('Active', 'active', 'bi-activity')
    elif post_count_value > 0 or profile_comment_count > 0:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('Getting Started', 'new', 'bi-person-check')
    else:
        profile_activity_status, profile_activity_tone, profile_activity_icon = ('New Member', 'new', 'bi-person')

    # Announcements (posts whose type name is 'Announcement')
    announcements = posts.filter(post_type__name__iexact='Announcement')[:5]

    is_owner = request.user == user

    # Role-based context for own profile
    is_site_staff = user.is_staff or user.is_superuser
    # Nests where the profile user is instructor or assistant
    managed_memberships = NestMembership.objects.filter(
        user=user,
        status=NestMembership.Status.ACTIVE,
        role__in=[NestMembership.Role.INSTRUCTOR, NestMembership.Role.ASSISTANT],
    ).select_related('nest')
    managed_nests = [m.nest for m in managed_memberships]
    is_nest_staff_anywhere = bool(managed_nests)

    if user.is_superuser or user.is_staff:
        profile_role_label = 'Site Staff'
    elif is_nest_staff_anywhere:
        profile_role_label = 'Nest Staff'
    else:
        profile_role_label = 'Member'

    # Pending nest requests created by this user (site-staff panel)
    from nests.models import Nest as NestModel
    from django.db.models import Count, Q as DQ
    if is_site_staff:
        pending_nest_requests = NestModel.objects.filter(status=NestModel.Status.PENDING).select_related('creator')
        site_staff_nest_stats = list(
            NestModel.objects.filter(status=NestModel.Status.APPROVED)
            .annotate(
                member_count=Count('memberships', filter=DQ(memberships__status='active'), distinct=True),
                post_count=Count('posts', distinct=True),
            ).order_by('name')
        )
        contact_unresolved = ContactMessage.objects.filter(is_resolved=False).count()
        open_reports_count = Report.objects.filter(is_resolved=False).count()
    else:
        pending_nest_requests = []
        site_staff_nest_stats = []
        contact_unresolved = 0
        open_reports_count = 0

    # Common nests (viewer and profile user share)
    common_nests = []
    if request.user.is_authenticated and not is_owner:
        viewer_nest_ids = set(
            NestMembership.objects.filter(
                user=request.user, status=NestMembership.Status.ACTIVE
            ).values_list('nest_id', flat=True)
        )
        common_nests = [n for n in nests if n.pk in viewer_nest_ids]

    return render(request, 'accounts/profile.html', {
        "user": user,
        "nests": nests,
        "nests_with_recognition": nests_with_recognition,
        "posts": posts[:5],
        "announcements": announcements,
        "post_count": post_count_value,
        "nest_count": len(nests),
        "is_owner": is_owner,
        "is_site_staff": is_site_staff,
        "is_nest_staff_anywhere": is_nest_staff_anywhere,
        "managed_nests": managed_nests,
        "pending_nest_requests": pending_nest_requests,
        "site_staff_nest_stats": site_staff_nest_stats,
        "common_nests": common_nests,
        "contact_unresolved": contact_unresolved,
        "open_reports_count": open_reports_count,
        "profile_comment_count": profile_comment_count,
        "profile_activity_status": profile_activity_status,
        "profile_activity_tone": profile_activity_tone,
        "profile_activity_icon": profile_activity_icon,
        "profile_role_label": profile_role_label,
    })

def update_user_profile(request:HttpRequest):

    if not request.user.is_authenticated:
        messages.warning(request, 'You must be signed in to edit your profile.', 'alert-warning')
        return redirect_to_login(request.get_full_path())
    

    if request.method == "POST":

        try:
            with transaction.atomic():
                user:User = request.user

                user.first_name = request.POST["first_name"]
                user.last_name = request.POST["last_name"]
                user.email = request.POST["email"]
                user.save()

                profile:Profile = user.profile
                profile.about = request.POST["about"]
                profile.social_link = request.POST["social_link"]
                profile.notify_in_app_post_updates = request.POST.get("notify_in_app_post_updates") == "on"
                profile.notify_email_post_updates = request.POST.get("notify_email_post_updates") == "on"
                profile.notify_in_app_announcements = request.POST.get("notify_in_app_announcements") == "on"
                profile.notify_email_announcements = request.POST.get("notify_email_announcements") == "on"
                if "avatar" in request.FILES: profile.avatar = request.FILES["avatar"]
                profile.save()

            messages.success(request, "updated profile successfuly", "alert-success")
        except Exception as e:
            messages.error(request, "Couldn't update profile", "alert-danger")
            print(e)

    return render(request, "accounts/update_profile.html")