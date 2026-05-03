from django.contrib import admin
from .models import Post, Comment, PostReadStatus, PostSubscription, PostType, PostTag, PostVote

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostType)
admin.site.register(PostTag)
admin.site.register(PostVote)
admin.site.register(PostSubscription)
admin.site.register(PostReadStatus)

# Register your models here.
