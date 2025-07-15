
from django import template
from django.db.models import Avg, Q
from syllabus.models import Subject, Chapter
from users.models import UserProgress

register = template.Library()

@register.inclusion_tag('core/_subject_progress_sidebar.html', takes_context=True)
def subject_progress_sidebar(context):
    """
    A custom inclusion tag to render the subject progress sidebar.
    It calculates the overall progress for each subject for the logged-in user.
    """
    user = context['request'].user
    
    # Return empty data if the user is not authenticated
    if not user.is_authenticated:
        return {'subjects_progress': []}

    subjects = Subject.objects.all()
    subjects_progress = []

    for subject in subjects:
        # Get all progress entries for the current user and subject
        user_progress_for_subject = UserProgress.objects.filter(
            user=user, 
            chapter__subject=subject
        )
        
        # Sum the progress for all chapters within that subject
        total_progress = sum(up.overall_progress for up in user_progress_for_subject)
        
        # Avoid division by zero if a subject has no chapters
        if subject.chapter_count > 0:
            # Calculate the average progress across all chapters for the subject
            average_progress = total_progress / subject.chapter_count
        else:
            average_progress = 0

        subjects_progress.append({
            'name': subject.name,
            'overall_progress': round(average_progress, 2)
        })

    return {'subjects_progress': subjects_progress}
