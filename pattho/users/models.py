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

    HSC_YEAR_CHOICES = [
        (2025, '2025'), 
        (2026, '2026'), 
        (2027, '2027'), 
        (2028, '2028')
    ]
    
    # Extend the default User model with additional fields
    stream = models.CharField(max_length=20, choices=STREAMS, default='hsc')
    show_on_leaderboard = models.BooleanField(default=True)
    avatar = models.URLField(blank=True, null=True)
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    college = models.CharField(max_length=100, blank=True, null=True)
    hscyear = models.PositiveIntegerField(blank=True, null=True, choices=HSC_YEAR_CHOICES)
    last_login_date = models.DateField(auto_now=True, null=True, blank=True)


    
    # Cached progress (updated via signals)
    overall_progress_cache = models.FloatField(default=0.0)

    @property
    def is_profile_complete(self):
        """
        Checks if all required profile fields are filled out.
        Returns True if the profile is complete, False otherwise.
        """
        if self.hscyear is None or not self.college:
            return False
        return True
    
    def __str__(self):
        return self.username



class UserProgress(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='progress', default=None)

    p_book = models.BooleanField(default=False, help_text="Class/concept done?")
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
        # Define weights for each field
        WEIGHT_THEORY = 0.10
        WEIGHT_NOTE = 0.20
        WEIGHT_MCQ = 0.20
        WEIGHT_CQ = 0.35
        WEIGHT_BOOK = 0.15 # Renamed to Class/Concept in display

        # Calculate weighted progress
        weighted_sum = 0
        if self.p_theory:
            weighted_sum += WEIGHT_THEORY
        if self.p_note:
            weighted_sum += WEIGHT_NOTE
        if self.p_mcq:
            weighted_sum += WEIGHT_MCQ
        if self.p_cq:
            weighted_sum += WEIGHT_CQ
        if self.p_book:
            weighted_sum += WEIGHT_BOOK

        return round(weighted_sum * 100, 2)

    def save(self, *args, **kwargs):
        self.overall_progress = self.calculate_overall_progress()
        print(f"Saving UserProgress for {self.user.username} - {self.chapter.title}: overall_progress={self.overall_progress}")
        super().save(*args, **kwargs)






