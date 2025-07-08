from django.urls import path
from . import views

urlpatterns = [
    path('todo/', views.todo_list, name='todo_list'),
    path('todo/add/', views.add_todo, name='add_todo'),
    path('api/todo/toggle/<int:todo_id>/', views.toggle_todo, name='toggle_todo'),
    path('api/task-summary/', views.get_task_summary, name='api_task_summary'),
    path('api/today-tasks/', views.get_today_tasks, name='api_today_tasks'),
]