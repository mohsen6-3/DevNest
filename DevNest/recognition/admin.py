from django.contrib import admin
from .models import NestRecognition


@admin.register(NestRecognition)
class NestRecognitionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'nest', 'title', 'badge', 'score', 'last_updated')
    list_filter   = ('nest', 'title', 'badge')
    search_fields = ('user__username', 'nest__name')
    ordering      = ('-score',)
    readonly_fields = ('last_updated',)
