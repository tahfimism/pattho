from django.urls import path
from .views import planner_view, delete_planner, update_planner

urlpatterns = [
    path('', planner_view, name='planner'),
    path('delete/', delete_planner, name='delete_planner'),
    path('update/', update_planner, name='update_planner'),
]