from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StudyRoutine
from syllabus.models import Subject, Chapter, Topic
from users.models import UserProfile
import datetime

@login_required
def delete_planner(request):
    if request.method == 'POST':
        user_routine = get_object_or_404(StudyRoutine, user=request.user)
        user_routine.delete()
    return redirect('planner')

@login_required
def update_planner(request):
    if request.method == 'POST':
        user_routine = get_object_or_404(StudyRoutine, user=request.user)
        completed_chapters = request.POST.getlist('completed_chapters')
        
        for date, chapters in user_routine.plan_data.items():
            for chapter in chapters:
                if chapter['chapter_title'] in completed_chapters:
                    chapter['completed'] = True
        
        user_routine.save()

    return redirect('planner')

def generate_study_plan(user, selected_chapters, start_date, total_days, daily_minutes, user_stream):
    total_available_minutes = total_days * daily_minutes

    topics = []
    for chapter in selected_chapters:
        for topic in chapter.topics.all():
            base_time = topic.chapter.recommended_time * 60 * (topic.time_percent / 100.0)
            importance_factor = topic.importance.get(user_stream, 50) / 100.0
            weight = base_time * importance_factor
            if weight > 0:
                topics.append({
                    'topic': topic,
                    'chapter': chapter,
                    'weight': weight
                })

    if not topics:
        return {}

    total_weight = sum(t['weight'] for t in topics)
    for t in topics:
        t['allocated_minutes'] = total_available_minutes * (t['weight'] / total_weight)

    plan_data = { 
        (start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): [] 
        for i in range(total_days) 
    }

    remaining_time_per_day = {i: float(daily_minutes) for i in range(total_days)}

    topic_queue = list(topics) # Create a mutable copy

    for day_index in range(total_days):
        current_date_str = (start_date + datetime.timedelta(days=day_index)).strftime('%Y-%m-%d')
        daily_chapters = {}
        
        # Iterate through a copy of the queue to avoid issues with modification during iteration
        for t in list(topic_queue):
            if remaining_time_per_day[day_index] <= 0: break

            time_to_assign = min(t['allocated_minutes'], remaining_time_per_day[day_index])

            if time_to_assign > 0:
                chapter_title = t['chapter'].title
                if chapter_title not in daily_chapters:
                    daily_chapters[chapter_title] = {
                        'chapter_title': chapter_title,
                        'completed': False,
                        'topics': []
                    }
                
                daily_chapters[chapter_title]['topics'].append({
                    'topic_title': t['topic'].title,
                    'allocated_minutes': round(time_to_assign)
                })
                
                t['allocated_minutes'] -= time_to_assign
                remaining_time_per_day[day_index] -= time_to_assign

                if t['allocated_minutes'] <= 0:
                    topic_queue.remove(t) # Remove fully allocated topic
        
        # Convert daily_chapters dict to list for plan_data
        plan_data[current_date_str] = list(daily_chapters.values())

    return plan_data

@login_required
def planner_view(request):
    try:
        user_routine = StudyRoutine.objects.get(user=request.user)
    except StudyRoutine.DoesNotExist:
        user_routine = None

    if request.method == 'POST' and 'daily_hours' in request.POST:
        daily_hours = float(request.POST.get('daily_hours'))
        daily_minutes = int(daily_hours * 60)
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        chapter_ids = request.POST.getlist('chapters')

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        total_days = (end_date - start_date).days + 1

        chapters = Chapter.objects.filter(id__in=chapter_ids)
        user_stream = request.user.stream

        plan_data = generate_study_plan(request.user, chapters, start_date, total_days, daily_minutes, user_stream)

        if not user_routine:
            user_routine = StudyRoutine.objects.create(
                user=request.user,
                daily_minutes=daily_minutes,
                start_date=start_date,
                end_date=end_date,
                plan_data=plan_data
            )
        else:
            user_routine.daily_minutes = daily_minutes
            user_routine.start_date = start_date
            user_routine.end_date = end_date
            user_routine.plan_data = plan_data
            user_routine.save()

        return redirect('planner')

    subjects = Subject.objects.all()
    context = {
        'user_routine': user_routine,
        'subjects': subjects
    }
    return render(request, 'planner/planner.html', context)