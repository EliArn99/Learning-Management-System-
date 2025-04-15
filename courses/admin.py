from django.contrib import admin
from .models import Course, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'university_name', 'teacher', 'slug')
    search_fields = ('name', 'university_name')
    list_filter = ('university_name', 'teacher')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('slug',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'slug')
    search_fields = ('student__user__username', 'course__name')
    list_filter = ('enrolled_at',)
    readonly_fields = ('slug',)
