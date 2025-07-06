from django.db import models
from django.contrib.auth.models import User


from syllabus.models import Topic, Chapter, Subject

# Create your models here.
class UserProfile(models.Model):
    
    STREAMS = [
        ('hsc', 'HSC'), 
        ('engineering', 'Engineering'), 
        ('medical', 'Medical'), 
        ('varsity', 'Varsity')
    ]
    
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stream = models.CharField(max_length=20, choices=STREAMS, default='hsc')
    show_on_leaderboard = models.BooleanField(default=True)
    avatar = models.URLField(blank=True, null=True)
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)

    
    # Cached progress (updated via signals)
    overall_progress_cache = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.user.username



class UserProgress(models.Model):

    STATUS_CHOICES = [
        ('NS', 'Not Started'),
        ('C', 'Completed'),
        ('R', 'Needs Revision'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='progress')

    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='NS')
    skip = models.BooleanField(default=False)

    personal_note = models.TextField(blank=True, null=True)

    # calculate time with js and just sum here, no need to store each session
    time_given = models.FloatField(help_text="Time given in hours")
    
    class Meta:
        unique_together = ('user', 'topic')
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.user.username} - {self.topic}"
