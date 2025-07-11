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
        completed_chapter_titles = request.POST.getlist('completed_chapters')
        completed_chapter_set = set(completed_chapter_titles)
        
        # Update the completion status within the existing plan_data
        for date_str, daily_chapters in user_routine.plan_data.items():
            for chapter_data in daily_chapters:
                chapter_title = chapter_data['chapter_title']
                # Mark chapter as completed if its title is in the completed_chapter_set
                chapter_data['completed'] = (chapter_title in completed_chapter_set)
                # Also mark all topics within this chapter as completed if the chapter is completed
                for topic_data in chapter_data['topics']:
                    topic_data['completed'] = chapter_data['completed'] # Topic completion follows chapter completion

        # Now, determine which chapters need to be replanned (i.e., are not completed)
        chapters_for_replan = []
        processed_chapter_titles = set() # To avoid adding duplicate Chapter objects

        for date_str, daily_chapters in user_routine.plan_data.items():
            for chapter_data in daily_chapters:
                chapter_title = chapter_data['chapter_title']
                # Only consider chapters that are not marked as completed and haven't been processed yet
                if not chapter_data['completed'] and chapter_title not in processed_chapter_titles:
                    try:
                        chapter_obj = Chapter.objects.get(title=chapter_title)
                        chapters_for_replan.append(chapter_obj)
                        processed_chapter_titles.add(chapter_title)
                    except Chapter.DoesNotExist:
                        continue # Skip if chapter not found

        if chapters_for_replan:
            start_date_for_replan = datetime.date.today()
            total_days_for_replan = (user_routine.end_date - start_date_for_replan).days + 1
            daily_minutes_for_replan = user_routine.daily_minutes

            if total_days_for_replan > 0:
                new_plan_data = generate_study_plan(
                    request.user, 
                    chapters_for_replan, 
                    start_date_for_replan, 
                    total_days_for_replan, 
                    daily_minutes_for_replan, 
                    request.user.stream
                )
                user_routine.plan_data = new_plan_data
            else:
                user_routine.plan_data = {} # No days left, clear plan
        else:
            user_routine.plan_data = {} # All chapters completed, clear plan

        user_routine.save()

    return redirect('planner')

def generate_study_plan(user, chapters_to_plan, start_date, total_days, daily_minutes, user_stream):
    total_available_minutes = total_days * daily_minutes

    chapters = []
    for chapter_obj in chapters_to_plan:
        # Calculate chapter weight
        recommended_hour = chapter_obj.recommended_time
        importance_factor = chapter_obj.importance.get(user_stream, 50) / 100.0 # Default to 50 if stream not found
        
        # weight = 0.7 * recommended_hour + (0.3 * importance[users stream] * recommended_hour)
        weight = (0.7 * recommended_hour) + (0.3 * importance_factor * recommended_hour)
        
        if weight > 0:
            chapters.append({
                'chapter': chapter_obj,
                'weight': weight,
                'topics': list(chapter_obj.topics.all()) # Get all topics for this chapter
            })

    if not chapters:
        return {}

    total_chapters_weight = sum(c['weight'] for c in chapters)
    
    # Allocate minutes to each chapter based on its weight
    for chapter_data in chapters:
        chapter_data['allocated_minutes'] = total_available_minutes * (chapter_data['weight'] / total_chapters_weight)
        
        # Now, distribute chapter's allocated minutes among its topics
        total_topic_percentage = sum(topic.time_percent for topic in chapter_data['topics'])
        if total_topic_percentage == 0: # Avoid division by zero if no topics or percentages are 0
            for topic in chapter_data['topics']:
                topic.allocated_minutes = 0
        else:
            for topic in chapter_data['topics']:
                topic.allocated_minutes = (chapter_data['allocated_minutes'] * (topic.time_percent / total_topic_percentage))

    plan_data = { 
        (start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): [] 
        for i in range(total_days) 
    }

    remaining_time_per_day = {i: float(daily_minutes) for i in range(total_days)}

    # Flatten all topics from all chapters into a single queue for daily assignment
    all_topics_queue = []
    for chapter_data in chapters:
        for topic in chapter_data['topics']:
            if topic.allocated_minutes > 0:
                all_topics_queue.append({
                    'topic': topic,
                    'chapter': chapter_data['chapter'],
                    'allocated_minutes': topic.allocated_minutes,
                    'completed': False # Initialize completion status
                })
    
    # Sort topics by their original chapter's weight or some other criteria if needed
    # For now, just use the order they were added (chapter by chapter, then topic by topic)
    
    topic_queue = list(all_topics_queue) # Create a mutable copy

    for day_index in range(total_days):
        current_date_str = (start_date + datetime.timedelta(days=day_index)).strftime('%Y-%m-%d')
        daily_chapters_data = {} # Use a dictionary to aggregate topics by chapter for the current day
        
        # Iterate through a copy of the queue to avoid issues with modification during iteration
        for t in list(topic_queue):
            if remaining_time_per_day[day_index] <= 0: break

            time_to_assign = min(t['allocated_minutes'], remaining_time_per_day[day_index])

            if time_to_assign > 0:
                chapter_title = t['chapter'].title
                topic_title = t['topic'].title

                if chapter_title not in daily_chapters_data:
                    daily_chapters_data[chapter_title] = {
                        'chapter_title': chapter_title,
                        'completed': False, # This will be updated by update_planner
                        'topics': {} # Use a dictionary for topics to easily update allocated_minutes
                    }
                
                if topic_title not in daily_chapters_data[chapter_title]['topics']:
                    daily_chapters_data[chapter_title]['topics'][topic_title] = {
                        'topic_title': topic_title,
                        'allocated_minutes': 0
                    }
                
                daily_chapters_data[chapter_title]['topics'][topic_title]['allocated_minutes'] += round(time_to_assign)
                
                t['allocated_minutes'] -= time_to_assign
                remaining_time_per_day[day_index] -= time_to_assign

                if t['allocated_minutes'] <= 0:
                    topic_queue.remove(t) # Remove fully allocated topic
        
        # Convert the nested dictionaries to lists for the final plan_data structure
        final_daily_chapters = []
        for chapter_title, chapter_content in daily_chapters_data.items():
            chapter_content['topics'] = list(chapter_content['topics'].values())
            final_daily_chapters.append(chapter_content)
            
        plan_data[current_date_str] = final_daily_chapters

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
                        'completed': topic_data.get('completed', False) # Use completion status from plan_data, default to False
                    }
                
                chapter_wise_plan[chapter_title]['topics'][topic_title]['planned_dates'].append({
                    'date': date_str,
                    'allocated_minutes': topic_data['allocated_minutes']
                })
                chapter_wise_plan[chapter_title]['topics'][topic_title]['total_allocated_minutes'] += topic_data['allocated_minutes']
    
    # Convert topics dictionary to a list for easier iteration in template
    for chapter_title, chapter_data in chapter_wise_plan.items():
        chapter_wise_plan[chapter_title]['topics'] = list(chapter_data['topics'].values())
        

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