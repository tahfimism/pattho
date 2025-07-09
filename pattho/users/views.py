from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Q
from .models import UserProfile, UserProgress
from syllabus.models import Subject, Chapter

# Helper function to calculate subject progress
def _calculate_subject_progress(user):
    """
    Calculates the overall progress for each subject for a given user.
    """
    subjects_progress = Subject.objects.annotate(
        overall_progress=Avg(
            'chapters__progress__overall_progress',
            filter=Q(chapters__progress__user=user)
        )
    ).values('name', 'overall_progress')

    formatted_progress = []
    for subject in subjects_progress:
        progress_value = subject['overall_progress'] if subject['overall_progress'] is not None else 0
        formatted_progress.append({
            'name': subject['name'],
            'overall_progress': round(progress_value, 2)
        })
    return formatted_progress

@login_required
def dashboard(request):
    user = request.user
    subjects = Subject.objects.all().prefetch_related('chapters')
    user_progress = UserProgress.objects.filter(user=user).values('chapter_id', 'p_book', 'p_note', 'p_mcq', 'p_cq', 'p_theory', 'overall_progress')

    progress_dict = {item['chapter_id']: item for item in user_progress}

    total_chapters = Chapter.objects.count()
    completed_chapters = UserProgress.objects.filter(user=user, overall_progress=100).count()
    in_progress_chapters = UserProgress.objects.filter(user=user, overall_progress__gt=0, overall_progress__lt=100).count()
    
    # Chapters that have no progress entry or have 0 overall_progress
    # Get all chapter IDs that have any progress entry (even 0%)
    chapters_with_progress_ids = UserProgress.objects.filter(user=user).values_list('chapter_id', flat=True)
    
    # Get all chapter IDs
    all_chapter_ids = Chapter.objects.values_list('id', flat=True)
    
    # Chapters that are truly not started (no entry in UserProgress)
    not_started_no_entry_count = len(set(all_chapter_ids) - set(chapters_with_progress_ids))
    
    # Chapters that have an entry but overall_progress is 0
    not_started_zero_progress_count = UserProgress.objects.filter(user=user, overall_progress=0).count()
    
    not_started_chapters = not_started_no_entry_count + not_started_zero_progress_count


    for subject in subjects:
        for chapter in subject.chapters.all():
            chapter.user_progress = progress_dict.get(chapter.id, {})

    return render(request, 'users/dashboard.html', {
        'subjects': subjects,
        'total_chapters': total_chapters,
        'completed_chapters': completed_chapters,
        'in_progress_chapters': in_progress_chapters,
        'not_started_chapters': not_started_chapters,
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
    formatted_progress = _calculate_subject_progress(request.user)
    return JsonResponse({'success': True, 'subjects_progress': formatted_progress})

@login_required
def analysis(request):
    """
    Renders the analysis page with charts for subject and overall progress.
    """
    subjects_progress_data = _calculate_subject_progress(request.user)

    total_progress = sum(subject['overall_progress'] for subject in subjects_progress_data)
    subject_count = len(subjects_progress_data)
    
    overall_average_progress = (total_progress / subject_count) if subject_count > 0 else 0

    # Calculate average progress for p_theory, p_book, p_note, p_cq, p_mcq
    user_progress_averages = UserProgress.objects.filter(user=request.user).aggregate(
        avg_p_theory=Avg('p_theory'),
        avg_p_book=Avg('p_book'),
        avg_p_note=Avg('p_note'),
        avg_p_cq=Avg('p_cq'),
        avg_p_mcq=Avg('p_mcq'),
    )

    # Convert averages to percentages and handle None if no progress entries exist
    p_theory_avg = round(user_progress_averages['avg_p_theory'] * 100, 2) if user_progress_averages['avg_p_theory'] is not None else 0
    p_book_avg = round(user_progress_averages['avg_p_book'] * 100, 2) if user_progress_averages['avg_p_book'] is not None else 0
    p_note_avg = round(user_progress_averages['avg_p_note'] * 100, 2) if user_progress_averages['avg_p_note'] is not None else 0
    p_cq_avg = round(user_progress_averages['avg_p_cq'] * 100, 2) if user_progress_averages['avg_p_cq'] is not None else 0
    p_mcq_avg = round(user_progress_averages['avg_p_mcq'] * 100, 2) if user_progress_averages['avg_p_mcq'] is not None else 0

    # --- New calculations for the 4 cards ---

    # Top Subject & Least Covered
    top_subject = None
    least_covered_subject = None
    if subjects_progress_data:
        # Filter out subjects with None progress before finding min/max
        valid_subjects = [s for s in subjects_progress_data if s['overall_progress'] is not None]
        if valid_subjects:
            top_subject = max(valid_subjects, key=lambda x: x['overall_progress'])
            least_covered_subject = min(valid_subjects, key=lambda x: x['overall_progress'])

    # Strongest Study Type & Needs Focus
    study_types = {
        'Theory': p_theory_avg,
        'Class/Concept': p_book_avg, # Use the display name here
        'Note': p_note_avg,
        'CQ': p_cq_avg,
        'MCQ': p_mcq_avg,
    }

    strongest_study_type = None
    needs_focus_study_type = None
    if study_types:
        # Filter out study types with None progress before finding min/max
        valid_study_types = {k: v for k, v in study_types.items() if v is not None}
        if valid_study_types:
            strongest_study_type = max(valid_study_types.items(), key=lambda item: item[1])
            needs_focus_study_type = min(valid_study_types.items(), key=lambda item: item[1])

    # --- New calculations for "Noted Chapter" and "Pending" ---
    noted_chapters_count = UserProgress.objects.filter(user=request.user, p_note=True).count()
    pending_chapters_count = UserProgress.objects.filter(user=request.user, p_note=False).count()
    # If a chapter has no UserProgress entry, it's also "pending" in terms of notes.
    # We need to get all chapters and subtract the ones that have a UserProgress entry.
    all_chapters_count = Chapter.objects.count()
    chapters_with_progress_entries = UserProgress.objects.filter(user=request.user).count()
    
    # Chapters that don't have a UserProgress entry yet are also considered pending for notes
    pending_chapters_count += (all_chapters_count - chapters_with_progress_entries)


    return render(request, 'users/analysis.html', {
        'subjects_progress': json.dumps(subjects_progress_data),
        'overall_average_progress': round(overall_average_progress, 2),
        'p_theory_avg': p_theory_avg,
        'p_book_avg': p_book_avg,
        'p_note_avg': p_note_avg,
        'p_cq_avg': p_cq_avg,
        'p_mcq_avg': p_mcq_avg,
        'top_subject': top_subject,
        'least_covered_subject': least_covered_subject,
        'strongest_study_type': strongest_study_type,
        'needs_focus_study_type': needs_focus_study_type,
        'noted_chapters_count': noted_chapters_count,
        'pending_chapters_count': pending_chapters_count,
    })
