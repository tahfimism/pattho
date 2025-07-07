
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
    for subject in subjects_progress:
        if subject['overall_progress'] is None:
            subject['overall_progress'] = 0
        else:
            subject['overall_progress'] = round(subject['overall_progress'], 2)

    return {'subjects_progress': subjects_progress}
