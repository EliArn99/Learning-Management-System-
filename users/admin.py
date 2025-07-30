from django.contrib import admin
from .models import CustomUser, StudentProfile, TeacherProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_superuser', 'is_active')
    list_filter = ('is_student', 'is_teacher', 'is_superuser', 'is_active') # Added is_active to filter
    search_fields = ('username', 'email')



@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'faculty_number', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'faculty_number')
    actions = ['approve_students']

    def approve_students(self, request, queryset):
        updated_count = queryset.update(is_approved=True)
        self.message_user(request, f"{updated_count} студентски профил/а беше/ха одобрен/и успешно.")
    approve_students.short_description = "Одобри избрани студентски профили"


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'education', 'experience_years', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'education')
    actions = ['approve_teachers']

    def approve_teachers(self, request, queryset):
        """Action to set selected teacher profiles to is_approved=True."""
        updated_count = queryset.update(is_approved=True)
        self.message_user(request, f"{updated_count} учителски профил/а беше/ха одобрен/и успешно.")
    approve_teachers.short_description = "Одобри избрани учителски профили"


# If you plan to use RegistrationCode later, this is fine
# @admin.register(RegistrationCode)
# class RegistrationCodeAdmin(admin.ModelAdmin):
#     list_display = ('code', 'is_used', 'user', 'created_at')
#     search_fields = ('code',)
