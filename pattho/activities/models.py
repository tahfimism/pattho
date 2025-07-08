from django.db import models
from django.utils import timezone
from users.models import UserProfile


# Create your models here.
# todo

class ToDoItem(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)
