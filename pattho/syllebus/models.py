from django.db import models

# Create your models here.

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.db.models import Count, F, GeneratedField



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



# syllabus

class Subject(models.Model):
    
    name = models.CharField(max_length=20)

    chapter_count = models.PositiveIntegerField(default=1)
    
        
    def __str__(self):
        return f"{self.grade} - {self.name}"


class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    chapter_number = models.PositiveIntegerField()

    topic_count = models.PositiveIntegerField(default=1)

    recommended_time = models.FloatField(help_text="Recommended study time in hours")

    # Stream-specific importance (0-100)
    importance = models.JSONField(
        default={
            'hsc': 0,
            'engineering': 0,
            'medical': 0,
            'varsity': 0
        }
    )
    
    
    class Meta:
        ordering = ['chapter_number']
        unique_together = ('subject', 'chapter_number')
    
    def __str__(self):
        return f"{self.subject.name}: {self.title}"



class Topic(models.Model):
    

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200,)
    order = models.PositiveIntegerField(help_text="Sequence in chapter")   
    description = models.TextField()

    resource_link =  models.TextField(blank=True) # comma separated if multiple

    
    # Stream-specific importance (0-100)
    importance = models.JSONField(
        default={
            'hsc': 10,
            'engineering': 10,
            'medical': 10,
            'varsity': 10
        }
    )
    
    

    time_percent = models.PositiveIntegerField(
        default=10, 
        help_text="Time percentage for this topic (0-100)", 
        validators=[MaxValueValidator(100)])

    
    class Meta:
        ordering = ['order']
        unique_together = ('chapter', 'order')
    
    def __str__(self):
        return f"{self.chapter.title} - {self.title}"



    

# progress


class UserProgress(models.Model):

    STATUS_CHOICES = [
        ('NS', 'Not Started'),
        ('C', 'Completed'),
        ('R', 'Needs Revision'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

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




# planner
class StudyRoutine(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
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



# todo
class ToDoItem(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)



    


# gamification 

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)  # icon name or path
    xp_reward = models.PositiveIntegerField(default=100)


class UserBadge(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'badge')


    