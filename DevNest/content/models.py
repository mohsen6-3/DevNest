from django.db import models
from django.conf import settings
import uuid


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Title(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey('content.Course', on_delete=models.CASCADE, related_name='titles')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Unit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Topic(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    TYPE_CHOICES = [
        ('video', 'Video'),
        ('file', 'File'),
        ('image', 'Image'),
        ('text', 'Text'),
        ('link', 'Link'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='contents')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.type} - {self.topic.name}"


class VideoContent(models.Model):
    content = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='video')
    video_url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    duration = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)
    resolution = models.CharField(max_length=20, default='1080p')

    def __str__(self):
        return f"Video: {self.content.topic.name}"


class FileContent(models.Model):
    content = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='file')
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_type = models.CharField(max_length=50)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    download_count = models.IntegerField(default=0)

    def __str__(self):
        return self.file_name


class ImageContent(models.Model):
    content = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='image')
    image_url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)

    def __str__(self):
        return self.alt_text or f"Image {self.id}"


class TextContent(models.Model):
    FORMAT_CHOICES = [
        ('plain', 'Plain Text'),
        ('markdown', 'Markdown'),
        ('html', 'HTML'),
        ('latex', 'LaTeX'),
    ]

    content = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='text')
    body = models.TextField()
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='markdown')

    def __str__(self):
        return f"Text: {self.body[:50]}"


class LinkContent(models.Model):
    content = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='link')
    url = models.URLField()
    display_text = models.CharField(max_length=255, blank=True)
    og_image = models.URLField(blank=True, null=True)
    og_title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.display_text or self.url


class ContentProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    progress_pct = models.FloatField(default=0.0)
    last_position = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'content']

    def __str__(self):
        return f"{self.user} - {self.content}"