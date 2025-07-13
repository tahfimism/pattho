from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StudyRoutine
from syllabus.models import Subject, Chapter, Topic
from users.models import UserProfile
import datetime
from django.contrib import messages

@login_required
def delete_planner(request):
    """
    Deletes the study routine for the logged-in user.
    This view expects a POST request.

    Args:
        request: HttpRequest object.

    Returns:
        HttpResponseRedirect: Redirects to the 'planner' page.
    """
    if request.method == 'POST':
        user_routine = get_object_or_404(StudyRoutine, user=request.user)
        user_routine.delete()
    return redirect('planner')

@login_required
def update_planner(request):
    """
    Updates the user's study plan based on completed chapters.
    This view expects a POST request.

    It processes completed chapters from the form, updates their status in the existing plan,
    and then regenerates the study plan for any remaining uncompleted chapters.

    Args:
        request: HttpRequest object containing POST data with 'completed_chapters'.

    Returns:
        HttpResponseRedirect: Redirects to the 'planner' page.
    """
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
                

        # Now, determine which chapters need to be replanned (i.e., are not completed)
        chapters_for_replan = []
        processed_chapter_titles = set() # To avoid adding duplicate Chapter objects

        for date_str, daily_chapters in user_routine.plan_data.items():
            for chapter_data in daily_chapters:
                chapter_title = chapter_data['chapter_title']
                # Only consider chapters that are not marked as completed and haven't been processed yet
                if not chapter_data['completed'] and chapter_title not in processed_chapter_titles:
                    try:
                        chapter_obj = Chapter.objects.filter(title=chapter_title).first()
                        chapters_for_replan.append(chapter_obj)
                        processed_chapter_titles.add(chapter_obj.title)
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
    """
    Generates a study plan by allocating study time to chapters based on their weighted importance.

    The weight of each chapter is calculated using its recommended study time and an importance factor
    specific to the user's academic stream. Chapters are assigned to days, ensuring that the total
    allocated time for each chapter is distributed across the available study days.

    Args:
        user (UserProfile): The user for whom the plan is being generated.
        chapters_to_plan (list): A list of Chapter objects to be included in the plan.
        start_date (datetime.date): The start date of the study plan.
        total_days (int): The total number of days available for study.
        daily_minutes (int): The number of minutes the user plans to study each day.
        user_stream (str): The academic stream of the user (e.g., 'Science', 'Commerce').

    Returns:
        dict: A dictionary where keys are dates (YYYY-MM-DD) and values are lists of dictionaries,
              each representing a chapter assigned to that day with its allocated minutes and topics.
              Returns an empty dictionary if no chapters are provided or no study time is available.
    """
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
        chapter_data['total_allocated_minutes'] = total_available_minutes * (chapter_data['weight'] / total_chapters_weight)
        chapter_data['remaining_allocated_minutes'] = chapter_data['total_allocated_minutes']

    plan_data = { 
        (start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): [] 
        for i in range(total_days) 
    }

    remaining_time_per_day = {i: float(daily_minutes) for i in range(total_days)}

    chapter_queue = list(chapters) # Create a mutable copy of chapters for daily assignment

    for day_index in range(total_days):
        current_date_str = (start_date + datetime.timedelta(days=day_index)).strftime('%Y-%m-%d')
        daily_chapters_data = {} # Use a dictionary to aggregate chapters for the current day
        
        # Iterate through a copy of the queue to avoid issues with modification during iteration
        for c in list(chapter_queue):
            if remaining_time_per_day[day_index] <= 0: break

            time_to_assign = min(c['remaining_allocated_minutes'], remaining_time_per_day[day_index])

            if time_to_assign > 0:
                chapter_title = c['chapter'].title

                if chapter_title not in daily_chapters_data:
                    daily_chapters_data[chapter_title] = {
                        'chapter_title': chapter_title,
                        'completed': False, # This will be updated by update_planner
                        'allocated_minutes_today': 0,
                        'topics': [t.title for t in c['topics']] # Just list topic titles
                    }
                
                daily_chapters_data[chapter_title]['allocated_minutes_today'] += round(time_to_assign)
                
                c['remaining_allocated_minutes'] -= time_to_assign
                remaining_time_per_day[day_index] -= time_to_assign

                if c['remaining_allocated_minutes'] <= 0:
                    chapter_queue.remove(c) # Remove fully allocated chapter
        
        # Convert the nested dictionaries to lists for the final plan_data structure
        final_daily_chapters = []
        for chapter_title, chapter_content in daily_chapters_data.items():
            final_daily_chapters.append(chapter_content)
            
        plan_data[current_date_str] = final_daily_chapters

    return plan_data

def get_chapter_wise_plan(plan_data):
    """
    Transforms the daily study plan data into a chapter-wise aggregated plan.

    This function takes the `plan_data` (which is structured by date) and reorganizes it
    to show all planned occurrences for each chapter, including total allocated minutes
    and a consolidated list of topics.

    Args:
        plan_data (dict): The study plan data structured by date, as generated by `generate_study_plan`.

    Returns:
        list: A list of dictionaries, where each dictionary represents a chapter
              and contains its title, topics, completion status, total allocated minutes,
              and a list of planned dates with their respective allocated minutes.
    """
    chapter_wise_plan = {}
    for date_str, daily_chapters in plan_data.items():
        for chapter_data in daily_chapters:
            chapter_title = chapter_data['chapter_title']
            if chapter_title not in chapter_wise_plan:
                chapter_wise_plan[chapter_title] = {
                    'chapter_title': chapter_title,
                    'topics': [],
                    'completed': chapter_data['completed'], # Initial completion status from first encounter
                    'total_allocated_minutes': 0 # Initialize total allocated minutes for the chapter
                }
            
            # Update chapter completion status if any daily entry marks it as complete
            if chapter_data['completed']:
                chapter_wise_plan[chapter_title]['completed'] = True

            for topic_title in chapter_data['topics']:
                if topic_title not in chapter_wise_plan[chapter_title]['topics']:
                    chapter_wise_plan[chapter_title]['topics'].append(topic_title)
            
            # Aggregate allocated minutes and planned dates at the chapter level
            if 'planned_dates' not in chapter_wise_plan[chapter_title]:
                chapter_wise_plan[chapter_title]['planned_dates'] = []
            chapter_wise_plan[chapter_title]['planned_dates'].append({
                'date': date_str,
                'allocated_minutes': chapter_data['allocated_minutes_today']
            })
            chapter_wise_plan[chapter_title]['total_allocated_minutes'] += chapter_data['allocated_minutes_today']
    
    # Convert topics dictionary to a list for easier iteration in template
    # The 'topics' are already a list of strings, no need for .values()
    # for chapter_title, chapter_data in chapter_wise_plan.items():
    #     chapter_wise_plan[chapter_title]['topics'] = list(chapter_data['topics'].values())
        

    return list(chapter_wise_plan.values())

@login_required
def planner_view(request):
    """
    Renders the study planner page. Handles the creation and display of study routines.

    If a POST request is received with 'daily_hours', it attempts to create or update
    the user's study routine based on the provided parameters (daily study hours,
    start/end dates, and selected chapters). It validates the input and generates
    a study plan.

    If a GET request is received, it displays the existing study plan for the user,
    including a chapter-wise breakdown and chapters planned for today.

    Args:
        request: HttpRequest object.

    Returns:
        HttpResponse: Renders the 'planner/planner.html' template with context data
                      related to the study plan, or redirects to the planner page
                      after a successful plan creation/update.
    """
    try:
        user_routine = StudyRoutine.objects.get(user=request.user)
    except StudyRoutine.DoesNotExist:
        user_routine = None

    chapter_wise_plan = None
    today_chapters = []
    if user_routine and user_routine.plan_data:
        chapter_wise_plan = get_chapter_wise_plan(user_routine.plan_data)
        today_date_str = datetime.date.today().strftime('%Y-%m-%d')
        today_chapters = user_routine.plan_data.get(today_date_str, [])

    if request.method == 'POST' and 'daily_hours' in request.POST:
        try:
            daily_hours = float(request.POST.get('daily_hours'))
            if daily_hours < 0.5:
                messages.error(request, "Daily study hours must be at least 0.5.")
                return redirect('planner')
        except (ValueError, TypeError):
            messages.error(request, "Invalid input for daily study hours.")
            return redirect('planner')

        daily_minutes = int(daily_hours * 60)
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        chapter_ids = request.POST.getlist('chapters')

        if not chapter_ids:
            messages.error(request, "You must select at least one chapter to study.")
            return redirect('planner')

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if start_date < datetime.date.today():
            messages.error(request, "Start date cannot be in the past.")
            return redirect('planner')

        if end_date < start_date:
            messages.error(request, "End date cannot be before the start date.")
            return redirect('planner')

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
        'today_chapters': today_chapters,
    }
    return render(request, 'planner/planner.html', context)