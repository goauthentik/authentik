"""OAuth Client User Creation Utils"""
from django.db.utils import IntegrityError

from passbook.core.models import User


def user_get_or_create(**kwargs: str) -> User:
    """Create user or return existing user"""
    try:
        new_user = User.objects.create_user(**kwargs)
    except IntegrityError:
        # At this point we've already checked that there is no existing connection
        # to any user. Hence if we can't create the user,
        kwargs["username"] = "%s_1" % kwargs["username"]
        new_user = User.objects.create_user(**kwargs)
    return new_user
