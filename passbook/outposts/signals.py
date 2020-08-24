"""passbook outpost signals"""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from passbook.outposts.models import Outpost


@receiver(pre_save, sender=Outpost)
# pylint: disable=unused-argument
def ensure_user_and_token(sender, instance, **_):
    """Ensure that token is created/updated on save"""
    _ = instance.token
