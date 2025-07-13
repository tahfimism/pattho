from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse


import json

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from users.models import UserProfile # Changed from User to UserProfile
from django.contrib import messages # Import messages framework

@login_required
def complete_profile_view(request):
    """
    Handles the profile completion form.
    Redirects to the dashboard if the profile is already complete.
    """
    if request.user.is_profile_complete:
        return HttpResponseRedirect(reverse('dashboard'))

    if request.method == 'POST':
        user_profile = request.user
        user_profile.hscyear = request.POST.get('hscyear')
        user_profile.college = request.POST.get('college')
        user_profile.save()
        messages.success(request, 'Profile completed successfully!')
        return HttpResponseRedirect(reverse('dashboard'))

    return render(request, 'core/complete_profile.html')

@login_required
def profile_view(request):
    """
    Handles the user profile view and updates. Allows users to update their username,
    first name, last name, and college. Displays success or error messages.

    Args:
        request: HttpRequest object.

    Returns:
        HttpResponse: Renders the 'core/profile.html' template with user data
                      or redirects to the profile page after an update.
    """
    if request.method == 'POST':
        user_profile = request.user
        user_profile.username = request.POST.get('username', user_profile.username)
        user_profile.first_name = request.POST.get('first_name', user_profile.first_name)
        user_profile.last_name = request.POST.get('last_name', user_profile.last_name)
        user_profile.college = request.POST.get('college', user_profile.college)
        # Email is readonly, so no need to update from POST
        
        try:
            user_profile.save()
            messages.success(request, 'Profile updated successfully!')
        except IntegrityError:
            messages.error(request, 'Username already taken. Please choose a different username.')
        except Exception as e:
            messages.error(request, f'Error updating profile: {e}')
        
        return HttpResponseRedirect(reverse('profile'))
    
    # Clear messages on GET request
    storage = messages.get_messages(request)
    storage.used = True
    
    return render(request, 'core/profile.html')

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('dashboard')) # Assuming 'dashboard' is your dashboard URL
    else:
        return render(request, 'core/index.html')


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "core/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "core/login.html")
        


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "core/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = UserProfile.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "core/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "core/register.html")
