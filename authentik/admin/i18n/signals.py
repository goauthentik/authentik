"""i18n signals"""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from authentik.admin.i18n.catalog import CATALOG_STORE
from authentik.admin.i18n.models import BrandLocaleCatalog, LocaleCatalog
from authentik.brands.models import Brand


@receiver(post_save, sender=LocaleCatalog)
@receiver(post_delete, sender=LocaleCatalog)
@receiver(post_save, sender=BrandLocaleCatalog)
@receiver(post_delete, sender=BrandLocaleCatalog)
# Catalogs of the default brand are used outside of requests
@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
def invalidate_locale_catalogs(sender, **_):
    """Reload catalogs in all processes once the change is visible to them"""
    transaction.on_commit(CATALOG_STORE.invalidate)
