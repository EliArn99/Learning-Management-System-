from django.contrib import admin
from .models import CustomUser, StudentProfile, TeacherProfile

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_superuser')
    list_filter = ('is_student', 'is_teacher', 'is_superuser')
    search_fields = ('username', 'email')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'faculty_number', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'faculty_number')
    readonly_fields = ('faculty_number',)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'education', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'education')
