from school.models import Teacher


def get_teacher(*, user) -> Teacher | None:
    """Return the Teacher linked to `user`, or None."""
    return Teacher.objects.filter(user=user).first()
