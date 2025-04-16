from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'subject', 'timestamp', 'is_read', 'deleted')
    list_filter = ('is_read', 'deleted', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'subject')


