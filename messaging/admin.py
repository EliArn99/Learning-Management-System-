from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "subject", "timestamp", "is_read", "deleted")
    list_filter = ("is_read", "deleted", "timestamp")
    search_fields = ("sender__username", "receiver__username", "subject", "content")
    readonly_fields = ("timestamp",)

    actions = ["mark_read", "mark_unread", "soft_delete", "restore"]

    @admin.action(description="Mark selected messages as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected messages as unread")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)

    @admin.action(description="Soft delete selected messages")
    def soft_delete(self, request, queryset):
        queryset.update(deleted=True)

    @admin.action(description="Restore selected messages")
    def restore(self, request, queryset):
        queryset.update(deleted=False)
