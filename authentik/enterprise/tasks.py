"""Enterprise tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.enterprise.license import LicenseKey


@actor(description=_("Update enterprise license status."))
def enterprise_update_usage():
    LicenseKey.get_total().record_usage()
