"""brand models"""

from uuid import uuid4

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.admin.files.manager import FileManager
from authentik.admin.files.usage import FileUsage
from authentik.admin.files.validation import validate_file_name
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.lib.models import SerializerModel

LOGGER = get_logger()


class Brand(SerializerModel):
    """Single brand"""

    brand_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    domain = models.TextField(
        help_text=_(
            "Domain that activates this brand. Can be a superset, i.e. `a.b` for `aa.b` and `ba.b`"
        )
    )
    default = models.BooleanField(
        default=False,
    )

    branding_title = models.TextField(default="authentik")

    branding_logo = models.TextField(
        validators=[validate_file_name],
        default="/static/dist/assets/icons/icon_left_brand.svg",
    )
    branding_favicon = models.TextField(
        validators=[validate_file_name],
        default="/static/dist/assets/icons/icon.png",
    )
    branding_custom_css = models.TextField(default="", blank=True)
    branding_default_flow_background = models.TextField(
        validators=[validate_file_name],
        default="/static/dist/assets/images/flow_background.jpg",
    )

    flow_authentication = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_authentication"
    )
    flow_invalidation = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_invalidation"
    )
    flow_recovery = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_recovery"
    )
    flow_unenrollment = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_unenrollment"
    )
    flow_user_settings = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_user_settings"
    )
    flow_device_code = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="brand_device_code"
    )

    default_application = models.ForeignKey(
        "authentik_core.Application",
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "When set, external users will be redirected to this application after authenticating."
        ),
    )

    web_certificate = models.ForeignKey(
        CertificateKeyPair,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_("Web Certificate used by the authentik Core webserver."),
        related_name="+",
    )
    client_certificates = models.ManyToManyField(
        CertificateKeyPair,
        default=None,
        blank=True,
        help_text=_("Certificates used for client authentication."),
    )
    attributes = models.JSONField(default=dict, blank=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.media_manager = FileManager(FileUsage.MEDIA)

    def branding_logo_url(self) -> str:
        """Get branding_logo URL"""
        return self.media_manager.file_url(self.branding_logo)

    def branding_favicon_url(self) -> str:
        """Get branding_favicon URL"""
        return self.media_manager.file_url(self.branding_favicon)

    def branding_default_flow_background_url(self) -> str:
        """Get branding_default_flow_background URL"""
        return self.media_manager.file_url(self.branding_default_flow_background)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.brands.api import BrandSerializer

        return BrandSerializer

    @property
    def default_locale(self) -> str:
        """Get default locale"""
        try:
            return self.attributes.get("settings", {}).get("locale", "")

        except Exception as exc:  # noqa
            LOGGER.warning("Failed to get default locale", exc=exc)
            return ""

    def __str__(self) -> str:
        if self.default:
            return "Default brand"
        return f"Brand {self.domain}"

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        indexes = [
            models.Index(fields=["domain"]),
            models.Index(fields=["default"]),
        ]


class WebfingerProvider(models.Model):
    """Provider which supports webfinger discovery"""

    class Meta:
        abstract = True

    def webfinger(self, resource: str, request: HttpRequest) -> dict:
        raise NotImplementedError()
