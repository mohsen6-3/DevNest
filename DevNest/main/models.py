from django.db import models
from django.conf import settings


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    subject    = models.CharField(max_length=200)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    staff_reply = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='resolved_messages',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'


class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM           = 'spam',           'Spam'
        HARASSMENT     = 'harassment',     'Harassment'
        MISINFORMATION = 'misinformation', 'Misinformation'
        INAPPROPRIATE  = 'inappropriate',  'Inappropriate Content'
        OTHER          = 'other',          'Other'

    reporter  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_filed',
    )
    post    = models.ForeignKey(
        'posts.Post', null=True, blank=True, on_delete=models.CASCADE, related_name='reports',
    )
    comment = models.ForeignKey(
        'posts.Comment', null=True, blank=True, on_delete=models.CASCADE, related_name='reports',
    )
    reason      = models.CharField(max_length=30, choices=Reason.choices)
    details     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reports_resolved',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = f'Post #{self.post_id}' if self.post_id else f'Comment #{self.comment_id}'
        return f'Report on {target} by {self.reporter.username}'

    @property
    def target_nest(self):
        if self.post_id and self.post.nest_id:
            return self.post.nest
        if self.comment_id and self.comment.post.nest_id:
            return self.comment.post.nest
        return None

    @property
    def target_post(self):
        if self.post_id:
            return self.post
        if self.comment_id:
            return self.comment.post
        return None


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message[:60]}'
