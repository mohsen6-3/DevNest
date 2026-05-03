from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import redirect_to_login
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Profile
from django.db import transaction
from posts.models import Post
from nests.models import NestMembership
from recognition.models import NestRecognition
from main.models import ContactMessage, Report



# Create your views here.


def sign_up(request: HttpRequest):

    if request.method == "POST":

        try:
            new_user = User.objects.create_user(username=request.POST["username"],password=request.POST["password"],email=request.POST["email"], first_name=request.POST["first_name"], last_name=request.POST["last_name"])
            new_user.save()

            profile = new_user.profile
            profile.about = request.POST["about"]
            profile.social_link = request.POST["social_link"]
            profile.avatar = request.FILES.get("avatar", Profile.avatar.field.get_default())
            profile.save()
            messages.success(request, "Registered User Successfuly", "alert-success")
            return redirect("accounts:sign_in")
        except Exception as e:
            messages.error(request, "Couldn't register user. Try again", "alert-danger")
            print(e)
    
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
            return redirect("accounts:user_profile_view", user_name=user.username)
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
        "post_count": posts.count(),
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
                if "avatar" in request.FILES: profile.avatar = request.FILES["avatar"]
                profile.save()

            messages.success(request, "updated profile successfuly", "alert-success")
        except Exception as e:
            messages.error(request, "Couldn't update profile", "alert-danger")
            print(e)

    return render(request, "accounts/update_profile.html")