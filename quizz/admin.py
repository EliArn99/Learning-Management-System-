from django.contrib import admin
from .models import Quiz, Question, Answer, Submission, StudentAnswer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')
    inlines = [AnswerInline]

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_by', 'available_from', 'available_until', 'is_active')
    list_filter = ('course', 'available_from', 'available_until')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'score', 'submitted_at')
    list_filter = ('quiz', 'submitted_at')
    search_fields = ('student__username', 'quiz__title')

class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('submission', 'question', 'selected_answer')

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(StudentAnswer, StudentAnswerAdmin)
