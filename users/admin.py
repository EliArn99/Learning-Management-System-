from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'enrollment_date')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('enrollment_date',)
    ordering = ('-enrollment_date',)

    readonly_fields = ('enrollment_date',)  # показва полето само за четене

    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'enrollment_date')
        }),
    )







# from django.contrib import admin
# from .models import CustomUser, StudentProfile, TeacherProfile


# @admin.register(CustomUser)
# class CustomUserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_superuser')
#     list_filter = ('is_student', 'is_teacher', 'is_superuser')
#     search_fields = ('username', 'email')


# @admin.register(StudentProfile)
# class StudentProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'age', 'is_approved')
#     list_filter = ('is_approved',)
#     search_fields = ('user__username',)

# @admin.register(TeacherProfile)
# class TeacherProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'is_approved')   #age', 'education',
#     list_filter = ('is_approved',)
#     search_fields = ('user__username',)



