from django.contrib import admin
from .models import Assignment, Submission

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'topic', 'created_at', 'due_date', 'status')
    list_filter = ('course', 'due_date')
    search_fields = ('title', 'topic', 'course__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'due_date'

    def status(self, obj):
        return obj.status
    status.short_description = 'Status'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'grade', 'graded_at')
    list_filter = ('assignment', 'grade', 'graded_at')
    search_fields = ('assignment__title', 'student__user__username')
    readonly_fields = ('submitted_at', 'graded_at')
