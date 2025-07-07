
# Create your views here.
from django.shortcuts import render


from .models import UserProfile, UserProgress
from syllabus.models import Subject, Chapter, Topic








def dashboard(request):
    user_profile = request.user

    # Get all topics
    chapters = Chapter.objects.all().select_related('subject')


    # Get progress for current user as a dict: topic_id -> status
    progress_qs = UserProgress.objects.filter(user=request.user).select_related('chapter')

    # Create a dict: {chapter_id: progress_obj}
    progress_dict = {p.chapter.id: p for p in progress_qs}



    
    return render(request, 'users/dashboard.html', {
        "user" : user_profile,
        "syll" : Subject.objects.all(),
        "chapters": chapters,
        "prog": progress_dict,
    })


