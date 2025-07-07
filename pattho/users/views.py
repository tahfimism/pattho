from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Q # Import Avg and Q for aggregation

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
        changes = data.get('changes')

        if not changes:
            return JsonResponse({'success': False, 'error': 'No changes provided'}, status=400)

        new_progress = {}
        for chapter_id, fields in changes.items():
            chapter = get_object_or_404(Chapter, id=chapter_id)
            user_progress, created = UserProgress.objects.get_or_create(user=request.user, chapter=chapter)

            for field, status in fields.items():
                if hasattr(user_progress, field):
                    setattr(user_progress, field, status)
                else:
                    # Log this error, but continue processing other fields
                    print(f"Invalid field '{field}' for chapter {chapter_id}")

            user_progress.save()
            print(f"UserProgress saved for chapter {chapter_id}. New overall_progress: {user_progress.overall_progress}")
            new_progress[chapter_id] = user_progress.overall_progress

        return JsonResponse({'success': True, 'new_progress': new_progress})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_subject_progress(request):
    """
    API endpoint to get the overall progress for each subject for the logged-in user.
    """
    user = request.user

    # This is an efficient query that calculates the average progress for each subject
    # by looking at the progress of its chapters for the current user.
    subjects_progress = Subject.objects.annotate(
        overall_progress=Avg(
            'chapters__progress__overall_progress',
            filter=Q(chapters__progress__user=user)
        )
    ).values('name', 'overall_progress')

    # The result of the query will have overall_progress as None for subjects
    # where the user has made no progress. We'll default this to 0.
    # Also, round the progress to 2 decimal places.
    formatted_progress = []
    for subject in subjects_progress:
        progress_value = subject['overall_progress'] if subject['overall_progress'] is not None else 0
        formatted_progress.append({
            'name': subject['name'],
            'overall_progress': round(progress_value, 2)
        })

    return JsonResponse({'success': True, 'subjects_progress': formatted_progress})