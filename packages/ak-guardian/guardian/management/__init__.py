from django.contrib.auth import get_user_model
from django.db import DatabaseError, router
from django.db.models import signals
from django.utils.module_loading import import_string

from guardian.conf import settings as guardian_settings


def get_init_anonymous_user(User):
    """
    Returns User model instance that would be referenced by guardian when
    permissions are checked against users that haven't signed into the system.

    :param User: User model - result of ``django.contrib.auth.get_user_model``.
    """
    kwargs = {User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
    user = User(**kwargs)
    user.set_unusable_password()
    return user


def create_anonymous_user(sender, **kwargs):
    """
    Creates anonymous User instance with id and username from settings.
    """
    User = get_user_model()
    if not router.allow_migrate_model(kwargs["using"], User):
        return
    try:
        lookup = {User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
        # fixing #770
        User.objects.using(kwargs["using"]).filter(**lookup).only(User.USERNAME_FIELD).get()
    except User.DoesNotExist, DatabaseError:
        # Handle both cases: user doesn't exist AND table doesn't exist (rollback scenario)
        try:
            retrieve_anonymous_function = import_string(guardian_settings.GET_INIT_ANONYMOUS_USER)
            user = retrieve_anonymous_function(User)
            user.save(using=kwargs["using"])
        except DatabaseError:
            # If we still get a DatabaseError when trying to save,
            # it means the table doesn't exist (rollback scenario)
            # In this case, we should silently return as the migration
            # will handle user creation when it's run again
            return


# Only create an anonymous user if support is enabled.
if guardian_settings.ANONYMOUS_USER_NAME is not None:
    from django.apps import apps

    guardian_app = apps.get_app_config("guardian")
    signals.post_migrate.connect(
        create_anonymous_user,
        sender=guardian_app,
        dispatch_uid="guardian.management.create_anonymous_user",
    )
