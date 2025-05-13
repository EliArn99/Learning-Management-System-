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
def submit_assignment_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Взимаме StudentProfile
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=student_profile  # ✅ подаваме правилно
    )

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            return redirect('assignments:assignment_detail', pk=assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'assignments/submit_assignment.html', {
        'assignment': assignment,
        'form': form,
        'submission': submission
    })


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = None

    if request.user.is_authenticated and hasattr(request.user, 'studentprofile'):
        student_profile = request.user.studentprofile
        submission = Submission.objects.filter(student=student_profile, assignment=assignment).first()

    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission
    })


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
    courses = Course.objects.filter(teacher=teacher)  # Ограничаваме курсовете на този преподавател

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        course_id = request.POST.get("course")
        course = get_object_or_404(Course, id=course_id, teacher=teacher)

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.save()
            messages.success(request, "Успешно създаде ново задание.")
            return redirect('assignments:assignment_list')
    else:
        form = AssignmentForm()

    return render(request, 'assignments/create_assignment.html', {
        'form': form,
        'courses': courses,  # Списък с курсове за <select>
    })


@login_required
def edit_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if submission.student.user != request.user:
        messages.error(request, "Нямате право да редактирате тази задача.")
        return redirect('assignments:assignment_list')

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Успешно редактирахте заданието.")
            return redirect('assignments:assignment_detail', pk=submission.assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'assignments/edit_submission.html', {
        'form': form,
        'submission': submission
    })
