from django.contrib import admin
from .models import CustomUser, StudentProfile, TeacherProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_superuser')
    list_filter = ('is_student', 'is_teacher', 'is_superuser')
    search_fields = ('username', 'email')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username',)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved')   #age', 'education',
    list_filter = ('is_approved',)
    search_fields = ('user__username',)



