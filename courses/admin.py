from django.contrib import admin
from .models import Course, Enrollment, Module, ModuleCategory


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "university_name", "teacher", "price", "slug")
    search_fields = ("name", "university_name", "teacher__user__username")
    list_filter = ("university_name", "teacher")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "student", "enrolled_at", "is_paid", "transaction_id")
    search_fields = ("course__name", "student__user__username", "transaction_id")
    list_filter = ("course", "is_paid", "enrolled_at")
    readonly_fields = ("enrolled_at", "transaction_id")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "course", "category")
    search_fields = ("title", "code", "course__name")
    list_filter = ("category", "course")


@admin.register(ModuleCategory)
class ModuleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
