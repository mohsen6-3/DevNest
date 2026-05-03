from django.contrib import admin
from .models import ContactMessage, Report


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ['subject', 'name', 'email', 'created_at', 'is_resolved']
    list_filter   = ['is_resolved']
    search_fields = ['subject', 'name', 'email']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display  = ['reason', 'reporter', 'post', 'comment', 'created_at', 'is_resolved']
    list_filter   = ['reason', 'is_resolved']
    search_fields = ['reporter__username']
