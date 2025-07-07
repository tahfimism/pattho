from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

from syllabus.models import Topic, Chapter, Subject

# Create your models here.
class UserProfile(AbstractUser):
    
    STREAMS = [
        ('hsc', 'HSC'), 
        ('eng', 'Engineering'), 
        ('med', 'Medical'), 
        ('var', 'Varsity')
    ]
    
    # Extend the default User model with additional fields
    stream = models.CharField(max_length=20, choices=STREAMS, default='hsc')
    show_on_leaderboard = models.BooleanField(default=True)
    avatar = models.URLField(blank=True, null=True)
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)

    
    # Cached progress (updated via signals)
    overall_progress_cache = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.username



class UserProgress(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='progress', default=None)

    p_book = models.BooleanField(default=False, help_text="Is book read?")
    p_note = models.BooleanField(default=False, help_text="Has note?")
    p_mcq = models.BooleanField(default=False, help_text="Did MCQ practice?")
    p_cq = models.BooleanField(default=False, help_text="Did CQ practice?")
    p_theory = models.BooleanField(default=False, help_text="Theory completed?")

    overall_progress = models.FloatField(default=0.0, help_text="Overall progress in percentage")
    
    skip = models.BooleanField(default=False)
    personal_note = models.TextField(blank=True, null=True)

    time_given = models.FloatField(default=0.0, help_text="Time given in hours")
    
    class Meta:
        unique_together = ('user', 'chapter')

    def __str__(self):
        return f"{self.user.username} - {self.chapter}"

    def calculate_overall_progress(self):
        flags = [
            self.p_book,
            self.p_note,
            self.p_mcq,
            self.p_cq,
            self.p_theory
        ]
        total = len(flags)
        completed = sum(1 for f in flags if f)
        return round((completed / total) * 100, 2)

    def save(self, *args, **kwargs):
        self.overall_progress = self.calculate_overall_progress()
        super().save(*args, **kwargs)






