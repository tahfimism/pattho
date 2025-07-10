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