from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define URLs that don't require login
        self.public_urls = [
            reverse('index'),
            reverse('login'),
            reverse('register'),
            # Allauth URLs (e.g., social login, password reset)
            # It's safer to include the base allauth URL pattern
            # and let allauth handle its internal redirects.
            # We'll check for 'accounts/' prefix.
        ]

    def __call__(self, request):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            # Check if the requested path is a public URL or starts with 'accounts/'
            path = request.path_info
            if not any(path.startswith(url) for url in self.public_urls) and not path.startswith('/accounts/'):
                return redirect(settings.LOGIN_URL or reverse('login'))
        
        response = self.get_response(request)
        return response



class ProfileCompletionMiddleware:
    """
    Middleware to ensure that users have completed their profiles.

    If a user is authenticated and their profile is not complete,
    they are redirected to the 'complete_profile' page.
    This check is bypassed for the complete_profile page itself and the logout page
    to prevent a redirect loop.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and not request.user.is_profile_complete:
            if request.path not in [reverse('complete_profile'), reverse('logout')]:
                return redirect('complete_profile')

        return response
