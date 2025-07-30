# users/views.py

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404

from quizz.models import Quiz
from .forms import StudentRegisterForm, TeacherRegisterForm, StudentProfileForm, TeacherProfileForm, SubmissionGradeForm
from .models import StudentProfile, TeacherProfile, CustomUser # Ensure CustomUser is imported if you're using it here
from django.contrib.auth.decorators import login_required


@login_required
def student_profile_view(request):
    # Retrieve the profile, or create it if somehow it doesn't exist (though it should after registration)
    profile = get_object_or_404(StudentProfile, user=request.user)

    # --- CRITICAL ADDITION: Check for approval status ---
    if not profile.is_approved:
        return redirect('users:approval_pending')
    # --- END CRITICAL ADDITION ---

    if request.method == 'POST':
        # Use StudentProfileForm for editing existing profiles, not StudentRegisterForm
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile') # Redirect to generic profile view or specific student_profile
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = StudentProfileForm(instance=profile)

    # Get upcoming quizzes only if the user is approved and viewing their dashboard/profile
    upcoming_quizzes = []
    try:
        if profile.is_approved: # Only fetch if approved
            upcoming_quizzes = Quiz.objects.filter(course__students=request.user, is_active=True)
    except Exception as e:
        print("❗️Грешка при извличане на тестове:", e)


    return render(request, 'users/student_profile.html', {
        'form': form,
        'student': profile,
        'upcoming_quizzes': upcoming_quizzes
    })


@login_required
def teacher_profile_view(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)

    # --- CRITICAL ADDITION: Check for approval status ---
    if not profile.is_approved:
        return redirect('users:approval_pending')
    # --- END CRITICAL ADDITION ---

    if request.method == 'POST':
        # Use TeacherProfileForm for editing existing profiles, not TeacherRegisterForm
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile') # Redirect to generic profile view or specific teacher_profile
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'users/teacher_profile.html', {'form': form, 'teacher': profile})


@login_required
def approval_pending_view(request):
    """
    Renders the page indicating that the user's account is pending approval.
    Includes logic to redirect approved users to their respective dashboards.
    """
    user = request.user
    profile = None

    # Determine user type and fetch the correct profile
    if user.is_student:
        try:
            profile = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            # This case means a student user exists but no profile.
            # Handle gracefully, maybe redirect to create profile or show error.
            # For now, we'll let them see the pending page, though it's an inconsistent state.
            pass
    elif user.is_teacher:
        try:
            profile = TeacherProfile.objects.get(user=user)
        except TeacherProfile.DoesNotExist:
            # Same for teacher
            pass

    # If a profile exists and is approved, redirect to dashboard
    if profile and profile.is_approved:
        if user.is_student:
            return redirect('dashboards:student_dashboard')
        elif user.is_teacher:
            return redirect('dashboards:teacher_dashboard')

    # If no profile or not approved, render the pending page
    return render(request, 'users/account_approval_pending.html')


# --- START MODIFIED REGISTRATION VIEWS ---
def register_student(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_student = True
            user.is_active = True # Allows user to log in and see the pending page
            user.save()

            # Create StudentProfile and set is_approved to False by default
            StudentProfile.objects.create(
                user=user,
                age=form.cleaned_data['age'],
                is_approved=False # <--- THIS IS KEY! New students are NOT approved.
            )
            login(request, user) # Log the user in immediately
            messages.success(request, 'Успешна регистрация! Вашият акаунт очаква одобрение.')
            return redirect('users:approval_pending') # <--- Redirect to the approval pending page
        else:
            messages.error(request, 'Възникна грешка при регистрацията. Моля, проверете данните си.')
    else:
        form = StudentRegisterForm()
    return render(request, 'users/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_teacher = True
            user.is_active = True # Allows user to log in and see the pending page
            user.save()

            # Create TeacherProfile and set is_approved to False by default
            TeacherProfile.objects.create(
                user=user,
                is_approved=False # <--- THIS IS KEY! New teachers are NOT approved.
            )
            login(request, user) # Log the user in immediately
            messages.success(request, 'Успешна регистрация! Вашият акаунт очаква одобрение от администратор.')
            return redirect('users:approval_pending') # <--- Redirect to the approval pending page
        else:
            messages.error(request, 'Възникна грешка при регистрацията. Моля, проверете данните си.')
    else:
        form = TeacherRegisterForm()
    return render(request, 'users/register_teacher.html', {'form': form})
# --- END MODIFIED REGISTRATION VIEWS ---


def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Check approval status immediately after login
            if user.is_student:
                try:
                    profile = StudentProfile.objects.get(user=user)
                    if not profile.is_approved:
                        messages.warning(request, 'Вашият акаунт очаква одобрение от администратор.')
                        return redirect('users:approval_pending')
                    return redirect('dashboards:student_dashboard')
                except StudentProfile.DoesNotExist:
                    # Fallback if somehow a student user exists but no profile (shouldn't happen post-reg)
                    messages.error(request, 'Възникна грешка с профила ви. Моля, свържете се с администратор.')
                    return redirect('users:approval_pending') # Or home, or a dedicated error page

            elif user.is_teacher:
                try:
                    profile = TeacherProfile.objects.get(user=user)
                    if not profile.is_approved:
                        messages.warning(request, 'Вашият акаунт очаква одобрение от администратор.')
                        return redirect('users:approval_pending')
                    return redirect('dashboards:teacher_dashboard')
                except TeacherProfile.DoesNotExist:
                    # Fallback if somehow a teacher user exists but no profile
                    messages.error(request, 'Възникна грешка с профила ви. Моля, свържете се с администратор.')
                    return redirect('users:approval_pending') # Or home, or error page
            else:
                messages.info(request, 'Добре дошли!')
                return redirect('home') # For generic users or unknown types
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def custom_logout_view(request):
    logout(request)
    messages.info(request, 'Успешно излязохте от профила си.')
    return render(request, 'users/logout.html') # Or redirect to a public page like 'home' or 'login'


@login_required
def profile_view(request):
    user = request.user

    # Initial check for approval for general profile view
    profile = None
    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
        if not profile.is_approved:
            return redirect('users:approval_pending')
        # If approved, proceed to render student profile
        try:
            upcoming_quizzes = Quiz.objects.filter(course__students=user, is_active=True)
        except Exception as e:
            print("❗️Грешка при извличане на тестове:", e)
            upcoming_quizzes = []
        return render(request, 'users/student_profile.html', {
            'student': profile,
            'upcoming_quizzes': upcoming_quizzes
        })

    elif user.is_teacher:
        profile = get_object_or_404(TeacherProfile, user=user)
        if not profile.is_approved:
            return redirect('users:approval_pending')
        # If approved, proceed to render teacher profile
        return render(request, 'users/teacher_profile.html', {
            'teacher': profile
        })

    # If user is neither student nor teacher, or no profile found (though it should exist by now if logged in)
    messages.error(request, 'Невалиден тип потребител или профил не е намерен.')
    return redirect('home')


@login_required
def edit_profile_view(request):
    user = request.user
    profile = None
    ProfileForm = None

    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
        if not profile.is_approved: # Prevent editing unapproved profile
            return redirect('users:approval_pending')
        ProfileForm = StudentProfileForm
    elif user.is_teacher:
        profile = get_object_or_404(TeacherProfile, user=user)
        if not profile.is_approved: # Prevent editing unapproved profile
            return redirect('users:approval_pending')
        ProfileForm = TeacherProfileForm
    else:
        messages.error(request, 'Нямате право да редактирате профил.')
        return redirect('home')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})
