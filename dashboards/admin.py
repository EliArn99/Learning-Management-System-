from django.contrib import admin

from .models import DashboardNotification


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "level", "is_read", "created_at")
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("title", "message", "user__email", "user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
