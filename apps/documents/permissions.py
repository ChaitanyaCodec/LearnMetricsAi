from apps.accounts.models import User
from apps.students.models import StudentEnrollment
from apps.teachers.models import TeachingAssignment

from .models import Document


def is_documents_admin(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.role == User.Roles.ADMIN
    )


def teacher_can_upload_for_subject(user, subject):
    """
    A teacher may upload only for an active assignment that
    exactly matches the subject's course and semester.
    """
    if (
        not user.is_authenticated
        or not user.is_active
        or user.role != User.Roles.TEACHER
    ):
        return False

    return TeachingAssignment.objects.filter(
        teacher__user=user,
        subject=subject,
        semester_id=subject.semester_id,
        course_id=subject.semester.course_id,
        is_active=True,
    ).exists()


def student_can_access_subject(user, subject):
    """
    A student may access only subjects in an active enrollment.
    """
    if (
        not user.is_authenticated
        or not user.is_active
        or user.role != User.Roles.STUDENT
    ):
        return False

    return StudentEnrollment.objects.filter(
        student__user=user,
        course_id=subject.semester.course_id,
        semester_id=subject.semester_id,
        status=StudentEnrollment.Status.ACTIVE,
        is_active=True,
    ).exists()


def can_view_document(user, document):
    if is_documents_admin(user):
        return True

    if user.role == User.Roles.TEACHER:
        # Teachers can always see their own documents. They can see
        # approved subject documents for subjects they are assigned.
        return (
            document.created_by_id == user.id
            or (
                document.status != Document.Status.RETIRED
                and document.published_version_id is not None
                and document.is_active
                and teacher_can_upload_for_subject(
                    user,
                    document.subject,
                )
            )
        )

    if user.role == User.Roles.STUDENT:
        return (
            document.status != Document.Status.RETIRED
            and document.published_version_id is not None
            and document.is_active
            and student_can_access_subject(
                user,
                document.subject,
            )
        )

    return False


def can_manage_document(user, document):
    """
    Editing, new versions, and review submission are restricted
    to the creator or an administrator.
    """
    return (
        is_documents_admin(user)
        or (
            user.is_authenticated
            and user.is_active
            and user.role == User.Roles.TEACHER
            and document.created_by_id == user.id
        )
    )