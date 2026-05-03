from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Profile
from django.db import transaction



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
            return redirect("nests:nest_dashboard")
        else:
            print("user not found")
            messages.error(request, "Please try again. You credentials are wrong", "alert-danger")



    return render(request, "accounts/signin.html")


def log_out(request: HttpRequest):

    logout(request)
    messages.success(request, "logged out successfully", "alert-warning")

    return redirect("accounts:sign_in")

def user_profile_view(request:HttpRequest, user_name):

    try:
        user = User.objects.get(username=user_name)
    except Exception as e:
        print(e)
        return render(request,'404.html')
    

    return render(request, 'accounts/profile.html', {"user" : user, "nests": user.nest_set.all()})

def update_user_profile(request:HttpRequest):

    if not request.user.is_authenticated:
        messages.warning(request, "Only registered users can update their profile", "alert-warning")
        return redirect("accounts:sign_in")
    

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