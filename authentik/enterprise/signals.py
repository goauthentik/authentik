from django.dispatch import receiver

from authentik.api.v3.config import Capabilities, capabilities
from authentik.enterprise.models import is_licensed


@receiver(capabilities)
def enterprise_capabilities(sender, **_):
    if is_licensed():
        return Capabilities.IS_ENTERPRISE_LICENSED
    return None
