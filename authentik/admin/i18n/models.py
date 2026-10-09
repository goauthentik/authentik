"""i18n models"""

from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.lib.models import SerializerModel


class LocaleCatalog(SerializerModel):
    """Custom translations for a single locale, applied on top of the built-in translations
    of both the backend and the web interface.

    `messages` maps a source string (or, for the web interface, a message ID) to its
    translation, for example `{"Username": "Benutzerkennung"}`."""

    catalog_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True)
    locale = models.TextField(
        help_text=_("Locale code, for example `de` or `de-DE`."),
    )
    enabled = models.BooleanField(default=True)
    order = models.IntegerField(
        default=0,
        help_text=_(
            "Catalogs for the same locale are applied in ascending order, so when multiple "
            "catalogs translate the same message, the catalog with the highest order wins. "
            "Catalogs for a more specific locale (`de-AT`) always win over catalogs for "
            "the base language (`de`)."
        ),
    )
    messages = models.JSONField(default=dict, blank=True)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.admin.i18n.api import LocaleCatalogSerializer

        return LocaleCatalogSerializer

    def __str__(self) -> str:
        return f"Locale catalog {self.name} ({self.locale})"

    class Meta:
        verbose_name = _("Locale Catalog")
        verbose_name_plural = _("Locale Catalogs")
        indexes = [
            models.Index(fields=["locale", "enabled"]),
        ]
