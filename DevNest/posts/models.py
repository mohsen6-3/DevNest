from django.db import models
from django.contrib.auth.models import User

from nests.models import Nest


class PostType(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    post_type = models.ForeignKey(PostType, on_delete=models.CASCADE, default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on {self.created_at}'

