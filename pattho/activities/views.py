from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ToDoItem
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone

@login_required
def todo_list(request):
    todos = ToDoItem.objects.filter(user=request.user).order_by('-date')
    return render(request, 'activities/todo.html', {'todos': todos})

@login_required
@require_POST
def add_todo(request):
    title = request.POST.get('title')
    if title:
        ToDoItem.objects.create(user=request.user, title=title)
    return redirect('todo_list')

@login_required
@require_POST
def toggle_todo(request, todo_id):
    todo = ToDoItem.objects.get(id=todo_id, user=request.user)
    todo.completed = not todo.completed
    todo.save()
    return redirect('todo_list')

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