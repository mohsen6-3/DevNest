from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.svg')
    social_link = models.URLField(blank=True)
    notify_in_app_post_updates = models.BooleanField(default=True)
    notify_email_post_updates = models.BooleanField(default=True)
    notify_in_app_announcements = models.BooleanField(default=True)
    notify_email_announcements = models.BooleanField(default=True)

    @property
    def is_site_staff(self):
        return self.user.is_staff or self.user.is_superuser
    
    def __str__(self):
        return f'Profile {self.user.username}'