"""authentik tenants signals"""

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_tenants.utils import get_public_schema_name

from authentik.tenants.models import Tenant


@receiver(pre_delete, sender=Tenant)
def tenants_ensure_no_default_delete(sender, instance: Tenant, **kwargs):
    if instance.schema_name == get_public_schema_name():
        raise models.ProtectedError("Cannot delete schema public", instance)
