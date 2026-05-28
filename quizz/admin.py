from django.contrib import admin

from .models import Answer, Question, Quiz, StudentAnswer, StudentQuizAttempt, Submission


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    fields = ("text", "type", "points")
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "created_by",
        "available_from",
        "available_until",
        "time_limit",
        "num_questions_to_select",
        "is_active",
    )
    list_filter = (
        "course",
        "created_by",
        "available_from",
        "available_until",
    )
    search_fields = (
        "title",
        "description",
        "course__name",
        "created_by__user__username",
    )
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "quiz",
        "type",
        "points",
    )
    list_filter = (
        "quiz",
        "type",
    )
    search_fields = (
        "text",
        "quiz__title",
    )
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "question",
        "is_correct",
    )
    list_filter = (
        "is_correct",
        "question__quiz",
    )
    search_fields = (
        "text",
        "question__text",
    )


@admin.register(StudentQuizAttempt)
class StudentQuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "quiz",
        "student",
        "start_time",
        "is_complete",
    )
    list_filter = (
        "is_complete",
        "quiz",
        "start_time",
    )
    search_fields = (
        "student__username",
        "quiz__title",
    )
    readonly_fields = (
        "start_time",
        "selected_question_ids",
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "quiz",
        "student",
        "score",
        "submitted_at",
    )
    list_filter = (
        "quiz",
        "submitted_at",
    )
    search_fields = (
        "student__username",
        "quiz__title",
    )
    readonly_fields = (
        "submitted_at",
    )


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "question",
        "selected_answer",
        "points_awarded",
    )
    list_filter = (
        "question__quiz",
    )
    search_fields = (
        "submission__student__username",
        "question__text",
        "selected_answer__text",
    )
