from django.db import models

from django.utils import timezone
from users.models import UserProfile
from syllabus.models import Topic


# Create your models here.
# planner
class StudyRoutine(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='routine')
    daily_minutes = models.PositiveIntegerField(default=120)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()

    # This field stores all topic/chapter assignments per day
    plan_data = models.JSONField(default=dict)


    def __str__(self):
        return f"{self.user.username}'s Study Plan"



