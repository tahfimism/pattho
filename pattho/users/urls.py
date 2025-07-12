from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update_progress/', views.update_progress, name='update_progress'),
    path('analysis/', views.analysis, name='analysis'),
    path('api/update_streak/', views.update_streak, name='update_streak'),
    path('api/subject_breakdown_progress/', views.get_subject_breakdown_progress, name='subject_breakdown_progress'),
]
