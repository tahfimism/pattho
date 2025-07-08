from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ToDoItem
from django.views.decorators.http import require_POST

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