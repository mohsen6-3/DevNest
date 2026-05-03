from django.db import models
from django.contrib.auth.models import User

from nests.models import Nest


class Title(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='titles', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Unit(models.Model):
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
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

    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        SCHEDULED = 'scheduled', 'Scheduled'
        ARCHIVED = 'archived', 'Archived'

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class VideoContent(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    video_title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to="videos/")
    thumbnail = models.ImageField(upload_to="images/thumbnails/", blank=True)
    duration = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.video_title


class FileContent(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="files/")
    file_type = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.file_name


class ImageContent(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    image_title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="images/content/")
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.image_title or f"Image {self.id}"


class TextContent(models.Model):

    class FormatChoices(models.TextChoices):
        PLAIN = 'plain', 'Plain Text'
        MARKDOWN = 'markdown', 'Markdown'
        HTML = 'html', 'HTML'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    text_title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    format = models.CharField(max_length=20, choices=FormatChoices.choices, default=FormatChoices.PLAIN)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.text_title or f"Text {self.id}"


class LinkContent(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    display_text = models.CharField(max_length=255)
    url = models.URLField()
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.display_text