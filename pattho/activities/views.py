from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ToDoItem
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
import json

@login_required
def todo_list(request):
    todos = ToDoItem.objects.filter(user=request.user).order_by('completed', '-date')
    return render(request, 'activities/todo.html', {'todos': todos})

@login_required
def pomodoro_timer(request):
    return render(request, 'activities/pomodoro.html')

@login_required
@require_POST
def add_todo(request):
    title = request.POST.get('title')
    if title:
        ToDoItem.objects.create(user=request.user, title=title)
    return redirect('activities')

@login_required
@require_POST
def toggle_todo(request, todo_id):
    try:
        todo = ToDoItem.objects.get(id=todo_id, user=request.user)
        todo.completed = not todo.completed
        todo.save()
        return JsonResponse({'success': True, 'completed': todo.completed})
    except ToDoItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

@login_required
def get_task_summary(request):
    user_todos = ToDoItem.objects.filter(user=request.user)
    
    total_tasks = user_todos.count()
    completed_tasks = user_todos.filter(completed=True).count()
    
    today = timezone.localdate()
    due_today_tasks = user_todos.filter(completed=False, date__date=today).count()
    
    overdue_tasks = user_todos.filter(completed=False, date__date__lt=today).count()
    
    data = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'due_today_tasks': due_today_tasks,
        'overdue_tasks': overdue_tasks,
    }
    return JsonResponse(data)

@login_required
def get_incomplete_tasks(request):
    incomplete_tasks = ToDoItem.objects.filter(
        user=request.user,
        completed=False,
    ).order_by('date').values('id', 'title')
    
    tasks_list = list(incomplete_tasks)
    return JsonResponse({'incomplete_tasks': tasks_list})

@login_required
@require_POST
def edit_todo_title(request, todo_id):
    try:
        todo = ToDoItem.objects.get(id=todo_id, user=request.user)
        data = json.loads(request.body)
        new_title = data.get('title')
        if new_title:
            todo.title = new_title
            todo.save()
            return JsonResponse({'success': True, 'title': todo.title})
        return JsonResponse({'success': False, 'error': 'No title provided'}, status=400)
    except ToDoItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

@login_required
@require_POST
def delete_todo(request, todo_id):
    try:
        todo = ToDoItem.objects.get(id=todo_id, user=request.user)
        todo.delete()
        return JsonResponse({'success': True})
    except ToDoItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)