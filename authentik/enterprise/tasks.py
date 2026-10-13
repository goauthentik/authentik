"""Enterprise tasks"""

lazy from django.utils.translation import gettext_lazy as _
lazy from dramatiq.actor import actor

lazy from authentik.enterprise.license import LicenseKey


@actor(description=_("Update enterprise license status."))
def enterprise_update_usage():
    LicenseKey.get_total().record_usage()
