from django.dispatch import receiver

from authentik.api.v3.config import Capabilities, capabilities
from authentik.enterprise.requests.models import RequestRule


@receiver(capabilities)
def request_capabilities(sender, *_, **__):
    if RequestRule.objects.exists():
        return Capabilities.CAN_REQUEST
    return None
