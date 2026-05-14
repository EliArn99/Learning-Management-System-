from django.contrib import admin

from .models import Course, Enrollment, Module, ModuleCategory


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university_name",
        "teacher",
        "price",
        "slug",
        "created_at",
    )
    search_fields = (
        "name",
        "university_name",
        "teacher__user__username",
        "teacher__user__email",
    )
    list_filter = (
        "university_name",
        "teacher",
        "created_at",
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "student",
        "enrolled_at",
        "is_paid",
        "is_approved",
        "transaction_id",
    )
    search_fields = (
        "course__name",
        "student__user__username",
        "student__user__email",
        "transaction_id",
    )
    list_filter = (
        "course",
        "is_paid",
        "is_approved",
        "enrolled_at",
    )
    readonly_fields = ("enrolled_at", "transaction_id")
    ordering = ("-enrolled_at",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "course",
        "category",
        "created_at",
    )
    search_fields = (
        "title",
        "code",
        "course__name",
        "description",
    )
    list_filter = (
        "category",
        "course",
        "created_at",
    )
    readonly_fields = ("created_at",)


@admin.register(ModuleCategory)
class ModuleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
