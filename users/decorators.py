from django.shortcuts import redirect

def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_student:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_teacher:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
