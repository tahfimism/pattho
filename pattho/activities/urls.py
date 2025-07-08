from django.urls import path
from . import views

urlpatterns = [
    path('todo/', views.todo_list, name='todo_list'),
    path('todo/add/', views.add_todo, name='add_todo'),
    path('api/todo/toggle/<int:todo_id>/', views.toggle_todo, name='toggle_todo'),
    path('api/task-summary/', views.get_task_summary, name='api_task_summary'),
    path('api/incomplete-tasks/', views.get_incomplete_tasks, name='api_incomplete_tasks'),
    path('api/todo/edit/<int:todo_id>/', views.edit_todo_title, name='api_edit_todo_title'),
    path('api/todo/delete/<int:todo_id>/', views.delete_todo, name='api_delete_todo'),
]