from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from authentik.core.models import BackchannelProvider, Token, User
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import OAuth2Provider


class EventTypes(models.TextChoices):
    """SSF Event types supported by authentik"""

    CAEP_SESSION_REVOKED = "https://schemas.openid.net/secevent/caep/event-type/session-revoked"
    CAEP_CREDENTIAL_CHANGE = "https://schemas.openid.net/secevent/caep/event-type/credential-change"


class DeliveryMethods(models.TextChoices):
    """SSF Delivery methods"""

    RISC_PUSH = "https://schemas.openid.net/secevent/risc/delivery-method/push"
    RISC_POLL = "https://schemas.openid.net/secevent/risc/delivery-method/poll"


class SSFProvider(BackchannelProvider):
    """Shared Signals Framework"""

    signing_key = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("Signing Key"),
        on_delete=models.SET_NULL,
        null=True,
        help_text=_(
            "Key used to sign the tokens. Only required when JWT Algorithm is set to RS256."
        ),
    )

    oidc_auth_providers = models.ManyToManyField(OAuth2Provider, blank=True, default=None)

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

    @property
    def service_account_identifier(self) -> str:
        return f"ak-providers-ssf-{self.pk}"

    @property
    def serializer(self):
        from authentik.enterprise.providers.ssf.api.providers import SSFProviderSerializer

        return SSFProviderSerializer

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/scim.png")

    @property
    def component(self) -> str:
        return "ak-provider-ssf-form"

    class Meta:
        verbose_name = _("SSF Provider")
        verbose_name_plural = _("SSF Providers")


class Stream(models.Model):
    """SSF Stream"""

    uuid = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    provider = models.ForeignKey(SSFProvider, on_delete=models.CASCADE)

    delivery_method = models.TextField(choices=DeliveryMethods.choices)
    endpoint_url = models.TextField(null=True)

    events_requested = ArrayField(models.TextField(choices=EventTypes.choices), default=list)
    format = models.TextField()
    aud = ArrayField(models.TextField(), default=list)

    user_subjects = models.ManyToManyField(User, "UserStreamSubject")

    def __str__(self) -> str:
        return "SSF Stream"


class UserStreamSubject(models.Model):
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Stream subject {self.stream_id} to {self.user_id}"
