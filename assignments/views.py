from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.mail import send_mail
from courses.models import Course
from .models import Assignment, Submission
from .forms import AssignmentSubmissionForm, GradeSubmissionForm
from users.models import StudentProfile
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AssignmentForm


@login_required
def assignment_list_view(request):
    assignments = Assignment.objects.all().order_by('due_date')
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})


@login_required
def my_assignments_view(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    # Взимаме курсовете чрез Enrollment
    my_courses = Course.objects.filter(enrollments__student=student_profile).distinct()

    assignments = Assignment.objects.filter(course__in=my_courses).order_by('due_date')

    assignments_with_status = []
    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, student=student_profile).first()
        assignments_with_status.append({
            'assignment': assignment,
            'submission': submission,
        })

    return render(request, 'assignments/my_assignments.html', {'assignments_with_status': assignments_with_status})


@login_required
def submit_assignment_view(request):
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.cleaned_data['assignment']
            student_profile = get_object_or_404(StudentProfile, user=request.user)

            # Проверка: има ли вече предаване за това задание?
            existing_submission = Submission.objects.filter(assignment=assignment, student=student_profile).first()
            if existing_submission:
                messages.error(request, "Вече сте предали това задание!")
                return redirect('assignments:my_assignments')

            assignment_submission = form.save(commit=False)
            assignment_submission.student = student_profile
            assignment_submission.save()
            messages.success(request, "Успешно предадохте заданието!")
            return redirect('assignments:my_assignments')
    else:
        form = AssignmentSubmissionForm()
    return render(request, 'assignments/submit_assignment.html', {'form': form})


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    return render(request, 'assignments/assignment_detail.html', {'assignment': assignment})


def is_teacher(user):
    return hasattr(user, 'teacherprofile')


@user_passes_test(is_teacher)
def teacher_submissions_view(request):
    submissions = Submission.objects.all().order_by('-submitted_at')
    return render(request, 'assignments/teacher_submissions.html', {'submissions': submissions})


@user_passes_test(is_teacher)
def grade_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_at = timezone.now()
            graded_submission.save()

            # Изпращаме имейл
            student_email = submission.student.user.email
            send_mail(
                'Your Assignment Has Been Graded',
                f'Hello {submission.student.user.username},\n\nYour submission for "{submission.assignment.title}" has been graded. You received a {graded_submission.grade}.\n\nFeedback: {graded_submission.feedback}',
                'no-reply@yourplatform.com',  # Изпращач
                [student_email],
                fail_silently=True,
            )

            return redirect('assignments:teacher_submissions')
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, 'assignments/grade_submission.html', {'form': form, 'submission': submission})


@login_required
@user_passes_test(is_teacher)
def create_assignment_view(request):
    teacher = request.user.teacherprofile
    courses = Course.objects.filter(teacher=teacher)

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            course_id = request.POST.get('course')
            assignment.course = get_object_or_404(Course, id=course_id, teacher=teacher)
            assignment.save()
            messages.success(request, "Успешно създаде ново задание.")
            return redirect('assignments:assignment_list')
    else:
        form = AssignmentForm()

    return render(request, 'assignments/create_assignment.html', {
        'form': form,
        'courses': courses,
    })
