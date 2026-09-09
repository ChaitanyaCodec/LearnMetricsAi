from apps.accounts.models import User
from apps.students.models import StudentEnrollment
from apps.teachers.models import TeachingAssignment


def can_access_conversation_subject(user, subject):
    """
    Determine whether a user may use conversations for a subject.

    Conversation access is intentionally separate from document
    management permissions.

    Admins have unrestricted access.
    Teachers require an active teaching assignment.
    Students require an active enrollment.
    """

    if (
        user is None
        or not getattr(user, "is_authenticated", False)
        or not getattr(user, "is_active", False)
    ):
        return False

    if user.role == User.Roles.ADMIN:
        return True

    if user.role == User.Roles.TEACHER:
        return TeachingAssignment.objects.filter(
            teacher__user=user,
            subject=subject,
            semester_id=subject.semester_id,
            course_id=subject.semester.course_id,
            is_active=True,
        ).exists()

    if user.role == User.Roles.STUDENT:
        return StudentEnrollment.objects.filter(
            student__user=user,
            course_id=subject.semester.course_id,
            semester_id=subject.semester_id,
            status=StudentEnrollment.Status.ACTIVE,
            is_active=True,
        ).exists()

    return False