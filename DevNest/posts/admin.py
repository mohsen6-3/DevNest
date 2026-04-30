from django.contrib import admin
from .models import Post, Comment, PostType

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostType)

# Register your models here.
