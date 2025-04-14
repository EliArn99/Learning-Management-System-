from django.shortcuts import redirect
from users.models import StudentProfile, TeacherProfile

def student_dashboard(request):
    profile = StudentProfile.objects.get(user=request.user)
    if not profile.is_approved:
        return redirect('approval_pending')  # some "waiting for approval" page
    # ... show dashboard

def teacher_dashboard(request):
    profile = TeacherProfile.objects.get(user=request.user)
    if not profile.is_approved:
        return redirect('approval_pending')
    # ... show dashboard
