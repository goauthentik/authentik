from django.dispatch import receiver
from django.http import HttpRequest

from authentik.api.v3.config import Capabilities, capabilities


@receiver(capabilities)
def agent_capabilities(sender, *_, request: HttpRequest, **__):
    if request.user.is_authenticated and request.user.has_perm(
        "authentik_agents.add_agent_self_service"
    ):
        return Capabilities.CAN_AGENT_SELF_SERVICE
    return None
