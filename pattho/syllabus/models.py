from django.db import models

# Create your models here.


from django.core.validators import MaxValueValidator



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
        default=dict
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
        default=dict
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



    


    