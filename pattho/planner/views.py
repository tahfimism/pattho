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
        completed_topic_identifiers = request.POST.getlist('completed_topics')
        
        completed_topic_set = set(completed_topic_identifiers)
        
        # Collect all topics and their completion status
        all_topics_in_plan = []
        for date_str, daily_chapters in user_routine.plan_data.items():
            for chapter_data in daily_chapters:
                for topic_data in chapter_data['topics']:
                    topic_identifier = f"{chapter_data['chapter_title']}|{topic_data['topic_title']}"
                    topic_data['completed'] = (topic_identifier in completed_topic_set)
                    all_topics_in_plan.append({
                        'topic_title': topic_data['topic_title'],
                        'chapter_title': chapter_data['chapter_title'],
                        'allocated_minutes': topic_data['allocated_minutes'],
                        'completed': topic_data['completed']
                    })

        # Filter out completed topics and calculate remaining allocated minutes
        incomplete_topics = [t for t in all_topics_in_plan if not t['completed']]
        
        # Re-generate the plan only for incomplete topics
        if incomplete_topics:
            # We need to fetch the actual Topic and Chapter objects for generate_study_plan
            # This is a simplified approach; a more robust solution might involve storing IDs
            # or fetching them more efficiently.
            
            # Group incomplete topics by chapter title to fetch Chapter objects
            chapters_to_replan = {}
            for topic_info in incomplete_topics:
                chapter_title = topic_info['chapter_title']
                if chapter_title not in chapters_to_replan:
                    # Fetch the Chapter object
                    try:
                        chapter_obj = Chapter.objects.get(title=chapter_title)
                        chapters_to_replan[chapter_title] = chapter_obj
                    except Chapter.DoesNotExist:
                        # Handle case where chapter might not exist (e.g., data inconsistency)
                        continue
            
            # Create a list of Chapter objects for generate_study_plan
            selected_chapters_for_replan = list(chapters_to_replan.values())

            # Use current date as start date for replanning
            start_date_for_replan = datetime.date.today()
            # Assuming total_days and daily_minutes remain the same for replanning
            total_days_for_replan = (user_routine.end_date - start_date_for_replan).days + 1
            daily_minutes_for_replan = user_routine.daily_minutes

            # Only generate if there are chapters to replan and days remaining
            if selected_chapters_for_replan and total_days_for_replan > 0:
                new_plan_data = generate_study_plan(
                    request.user, 
                    selected_chapters_for_replan, 
                    start_date_for_replan, 
                    total_days_for_replan, 
                    daily_minutes_for_replan, 
                    request.user.stream
                )
                user_routine.plan_data = new_plan_data
            else:
                user_routine.plan_data = {} # No incomplete topics or no days left, clear plan
        else:
            user_routine.plan_data = {} # All topics completed, clear plan

        user_routine.save()

    return redirect('planner')

def generate_study_plan(user, topics_to_plan, start_date, total_days, daily_minutes, user_stream):
    total_available_minutes = total_days * daily_minutes

    topics = []
    for topic_obj in topics_to_plan:
        # If topic_obj is a dictionary (from incomplete_topics), convert it to a Topic object
        if isinstance(topic_obj, dict):
            try:
                topic = Topic.objects.get(title=topic_obj['topic_title'], chapter__title=topic_obj['chapter_title'])
            except Topic.DoesNotExist:
                continue # Skip if topic not found
        else:
            topic = topic_obj # Assume it's already a Topic object

        base_time = topic.chapter.recommended_time * 60 * (topic.time_percent / 100.0)
        importance_factor = topic.importance.get(user_stream, 50) / 100.0
        weight = base_time * importance_factor
        if weight > 0:
            topics.append({
                'topic': topic,
                'chapter': topic.chapter,
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

def get_chapter_wise_plan(plan_data):
    chapter_wise_plan = {}
    for date_str, daily_chapters in plan_data.items():
        for chapter_data in daily_chapters:
            chapter_title = chapter_data['chapter_title']
            if chapter_title not in chapter_wise_plan:
                chapter_wise_plan[chapter_title] = {
                    'chapter_title': chapter_title,
                    'topics': {},
                    'completed': chapter_data['completed'] # Initial completion status from first encounter
                }
            
            # Update chapter completion status if any daily entry marks it as complete
            if chapter_data['completed']:
                chapter_wise_plan[chapter_title]['completed'] = True

            for topic_data in chapter_data['topics']:
                topic_title = topic_data['topic_title']
                if topic_title not in chapter_wise_plan[chapter_title]['topics']:
                    chapter_wise_plan[chapter_title]['topics'][topic_title] = {
                        'topic_title': topic_title,
                        'planned_dates': [],
                        'total_allocated_minutes': 0,
                        'completed': False # Initial completion status
                    }
                
                chapter_wise_plan[chapter_title]['topics'][topic_title]['planned_dates'].append({
                    'date': date_str,
                    'allocated_minutes': topic_data['allocated_minutes']
                })
                chapter_wise_plan[chapter_title]['topics'][topic_title]['total_allocated_minutes'] += topic_data['allocated_minutes']
    
    # Convert topics dictionary to a list for easier iteration in template
    for chapter_title, chapter_data in chapter_wise_plan.items():
        chapter_wise_plan[chapter_title]['topics'] = list(chapter_data['topics'].values())
        # Determine overall topic completion (if all planned dates for a topic are completed)
        for topic in chapter_wise_plan[chapter_title]['topics']:
            topic['completed'] = topic_data.get('completed', False)

    return list(chapter_wise_plan.values())

@login_required
def planner_view(request):
    try:
        user_routine = StudyRoutine.objects.get(user=request.user)
    except StudyRoutine.DoesNotExist:
        user_routine = None

    chapter_wise_plan = None
    if user_routine and user_routine.plan_data:
        chapter_wise_plan = get_chapter_wise_plan(user_routine.plan_data)

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
        all_topics_from_selected_chapters = []
        for chapter in chapters:
            all_topics_from_selected_chapters.extend(list(chapter.topics.all()))
        user_stream = request.user.stream

        plan_data = generate_study_plan(request.user, all_topics_from_selected_chapters, start_date, total_days, daily_minutes, user_stream)

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
        
        # After saving, regenerate chapter_wise_plan for immediate display
        chapter_wise_plan = get_chapter_wise_plan(user_routine.plan_data)

        return redirect('planner')

    subjects = Subject.objects.all()
    context = {
        'user_routine': user_routine,
        'subjects': subjects,
        'chapter_wise_plan': chapter_wise_plan,
    }
    return render(request, 'planner/planner.html', context)