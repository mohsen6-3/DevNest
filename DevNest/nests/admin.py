from django.contrib import admin

from .models import Nest, NestMembership


@admin.register(Nest)
class NestAdmin(admin.ModelAdmin):
    list_display  = ('name', 'creator', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('name', 'creator__username')


@admin.register(NestMembership)
class NestMembershipAdmin(admin.ModelAdmin):
    list_display  = ('nest', 'user', 'role', 'status', 'joined_at')
    list_filter   = ('role', 'status')
    search_fields = ('nest__name', 'user__username')
