from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, UserProgress
from syllabus.models import Subject, Chapter

@login_required
def dashboard(request):
    user = request.user
    subjects = Subject.objects.all().prefetch_related('chapters')
    user_progress = UserProgress.objects.filter(user=user).values('chapter_id', 'p_book', 'p_note', 'p_mcq', 'p_cq', 'p_theory', 'overall_progress')

    progress_dict = {item['chapter_id']: item for item in user_progress}

    for subject in subjects:
        for chapter in subject.chapters.all():
            chapter.user_progress = progress_dict.get(chapter.id, {})

    return render(request, 'users/dashboard.html', {
        'subjects': subjects,
    })

@login_required
@require_POST
@csrf_exempt
def update_progress(request):
    try:
        data = json.loads(request.body)
        chapter_id = data.get('chapter_id')
        field = data.get('field')
        status = data.get('status')

        if chapter_id is None or field is None or status is None:
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        chapter = get_object_or_404(Chapter, id=chapter_id)
        user_progress, created = UserProgress.objects.get_or_create(user=request.user, chapter=chapter)

        if hasattr(user_progress, field):
            setattr(user_progress, field, status)
            user_progress.save()
            return JsonResponse({'success': True, 'new_progress': user_progress.overall_progress})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)