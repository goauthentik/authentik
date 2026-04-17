"""Enterprise tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.enterprise.license import LicenseKey


def _deactivate_agent_users():
    """Mark all active agent users inactive and remove their sessions when the enterprise
    license is not valid. Called after each license usage recording."""
    from authentik.core.models import (
        USER_ATTRIBUTE_AGENT_OWNER_PK,
        Session,
        User,
    )

    agents = User.objects.filter(
        attributes__has_key=USER_ATTRIBUTE_AGENT_OWNER_PK,
        is_active=True,
    )
    Session.objects.filter(authenticatedsession__user__in=agents).delete()
    agents.update(is_active=False)


@actor(description=_("Update enterprise license status."))
def enterprise_update_usage():
    usage = LicenseKey.get_total().record_usage()
    if not usage.status.is_valid:
        _deactivate_agent_users()
