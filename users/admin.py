from django.contrib import admin

# Register your models here.
# in users/admin.py
from django.contrib import admin
from .models import StudentProfile

class StudentProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('faculty_number',)

    def save_model(self, request, obj, form, change):
        if not obj.faculty_number:
            obj.faculty_number = f"STD-{obj.user.id:05}"
        super().save_model(request, obj, form, change)

admin.site.register(StudentProfile, StudentProfileAdmin)
