from django.db import models
from users.models import UserProfile

# Create your models here.
# gamification 

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)  # icon name or path
    xp_reward = models.PositiveIntegerField(default=100)


class UserBadge(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')

    class Meta:
        unique_together = ('user', 'badge')

