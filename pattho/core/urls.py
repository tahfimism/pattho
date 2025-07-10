from django.urls import path
from django.urls import include
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("complete-profile/", views.complete_profile_view, name="complete_profile"),
]