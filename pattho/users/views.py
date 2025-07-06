
# Create your views here.
from django.shortcuts import render
from progress.utils import get_user_progress
from planner.utils import get_daily_tasks
from gamification.utils import get_user_xp

def dashboard(request):
    user_profile = request.user.userprofile
    context = {
        'progress': get_user_progress(user_profile),
        'tasks': get_daily_tasks(user_profile),
        'xp': get_user_xp(user_profile),
        'streak': user_profile.streak
    }
    return render(request, 'users/dashboard.html', context)