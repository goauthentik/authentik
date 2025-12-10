from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

ANONYMOUS_USER_NAME = getattr(settings, "GUARDIAN_ANONYMOUS_USER_NAME", "AnonymousUser")
GET_INIT_ANONYMOUS_USER = getattr(
    settings, "GUARDIAN_GET_INIT_ANONYMOUS_USER", "guardian.management.get_init_anonymous_user"
)
GET_CONTENT_TYPE = getattr(
    settings, "GUARDIAN_GET_CONTENT_TYPE", "guardian.ctypes.get_default_content_type"
)
# Anonymous user cache TTL configuration
# 0 = no cache (default), positive number = cache TTL in seconds, -1 = cache indefinitely
ANONYMOUS_USER_CACHE_TTL = getattr(settings, "GUARDIAN_ANONYMOUS_USER_CACHE_TTL", 0)
# Default to using guardian supplied generic object permission models
USER_OBJ_PERMS_MODEL = getattr(
    settings, "GUARDIAN_USER_OBJ_PERMS_MODEL", "guardian.UserObjectPermission"
)
GROUP_OBJ_PERMS_MODEL = getattr(
    settings, "GUARDIAN_GROUP_OBJ_PERMS_MODEL", "guardian.GroupObjectPermission"
)
ROLE_OBJ_PERMS_MODEL = getattr(
    settings, "GUARDIAN_ROLE_OBJ_PERMS_MODEL", "guardian.RoleObjectPermission"
)

# Since get_user_model() causes a circular import if called when app models are
# being loaded, the user_model_label should be used when possible, with calls
# to get_user_model deferred to execution time
user_model_label = getattr(settings, "AUTH_USER_MODEL", "auth.User")
role_model_label = getattr(settings, "GUARDIAN_ROLE_MODEL", None)
if role_model_label is None:
    raise ImproperlyConfigured("ak-guardian requires settings.GUARDIAN_ROLE_MODEL")
