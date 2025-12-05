from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission


def _add_perm(user, codename: str, app_label: str):
    permission = Permission.objects.get(codename=codename, content_type__app_label=app_label)
    user.user_permissions.add(permission)
    user.save()


def _drop_perm(user, codename: str, app_label: str):
    permission = Permission.objects.get(codename=codename, content_type__app_label=app_label)
    user.user_permissions.remove(permission)
    user.save()


patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)
