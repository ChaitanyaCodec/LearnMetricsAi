from django.contrib.auth.decorators import login_required


def administrator_required(view_func):
    return login_required(view_func)


def teacher_required(view_func):
    return login_required(view_func)


def student_required(view_func):
    return login_required(view_func)