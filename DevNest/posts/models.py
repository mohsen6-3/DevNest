from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from nests.models import Nest


class PostType(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class PostTag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    post_type = models.ForeignKey(PostType, on_delete=models.CASCADE, default=None, null=True, blank=True)
    tags = models.ManyToManyField(PostTag, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PostVote(models.Model):
    class Value(models.IntegerChoices):
        DOWN = -1, 'Downvote'
        UP = 1, 'Upvote'

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_votes')
    value = models.SmallIntegerField(choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_vote'),
        ]

    def __str__(self):
        return f'{self.user.username} {self.value:+d} on {self.post_id}'


class PostSubscription(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_subscriptions')
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_subscription'),
        ]

    def __str__(self):
        state = 'on' if self.is_enabled else 'off'
        return f'{self.user.username} subscription {state} on {self.post_id}'


class PostReadStatus(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_read_statuses')
    read_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_read_status'),
        ]

    def __str__(self):
        return f'{self.user.username} read post {self.post_id}'


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

