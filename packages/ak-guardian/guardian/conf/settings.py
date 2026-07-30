from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

ANONYMOUS_USER_NAME = getattr(settings, "GUARDIAN_ANONYMOUS_USER_NAME", "AnonymousUser")
GET_INIT_ANONYMOUS_USER = getattr(
    settings, "GUARDIAN_GET_INIT_ANONYMOUS_USER", "guardian.management.get_init_anonymous_user"
)
# Anonymous user cache TTL configuration
# 0 = no cache (default), positive number = cache TTL in seconds, -1 = cache indefinitely
ANONYMOUS_USER_CACHE_TTL = getattr(settings, "GUARDIAN_ANONYMOUS_USER_CACHE_TTL", 0)

group_model_label = getattr(settings, "GUARDIAN_GROUP_MODEL", None)
role_model_label = getattr(settings, "GUARDIAN_ROLE_MODEL", None)
if group_model_label is None:
    raise ImproperlyConfigured("ak-guardian requires settings.GUARDIAN_GROUP_MODEL")
if role_model_label is None:
    raise ImproperlyConfigured("ak-guardian requires settings.GUARDIAN_ROLE_MODEL")
