from functools import wraps

from django.core.exceptions import PermissionDenied


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Само студенти имат достъп до тази страница.")
        return view_func(request, *args, **kwargs)

    return wrapper


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "teacherprofile"):
            raise PermissionDenied("Само преподаватели имат достъп до тази страница.")
        return view_func(request, *args, **kwargs)

    return wrapper