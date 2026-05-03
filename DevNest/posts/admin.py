from django.contrib import admin
from .models import Post, Comment, PostType, PostTag, PostVote

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostType)
admin.site.register(PostTag)
admin.site.register(PostVote)

# Register your models here.
