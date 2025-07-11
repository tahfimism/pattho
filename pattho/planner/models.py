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

    def __str__(self):
        return f"{self.user.username}'s Study Plan"


class PlannedTask(models.Model):
    routine = models.ForeignKey(StudyRoutine, on_delete=models.CASCADE, related_name='tasks')
    date = models.DateField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    allocated_minutes = models.PositiveIntegerField()
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']
