"""
OAuth Client User Creation Utils
"""

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError


def user_get_or_create(user_model=None, **kwargs):
    """Create user or return existing user"""
    if user_model is None:
        user_model = get_user_model()
    try:
        new_user = user_model.objects.create_user(**kwargs)
    except IntegrityError:
        new_user = user_model.objects.get(username=kwargs['username'])
    return new_user
