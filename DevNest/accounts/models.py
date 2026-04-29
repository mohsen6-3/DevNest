from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.svg')
    social_link = models.URLField(blank=True)
    
    def __str__(self):
        return f'Profile {self.user.username}'