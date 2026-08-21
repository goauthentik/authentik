"""Duo stage"""

from os import chmod
from tempfile import NamedTemporaryFile, mkdtemp

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from duo_client.admin import Admin
from duo_client.auth import Auth
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.types import UserSettingSerializer
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.models import SerializerModel
from authentik.lib.utils.http import authentik_user_agent
from authentik.stages.authenticator.models import Device


class AuthenticatorDuoStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Duo authentication for the user."""

    api_hostname = models.TextField()

    client_id = models.TextField()
    client_secret = models.TextField()

    admin_integration_key = models.TextField(blank=True, default="")
    admin_secret_key = models.TextField(blank=True, default="")

    ca_chain = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="duo_ca_chains",
        help_text=_(
            "Optionally verify the Duo API server's certificate against the CA Chain in this "
            "keypair, instead of the CA bundle shipped with the Duo client. Required when Duo "
            "is reached through a TLS-inspecting proxy that re-signs with an internal CA."
        ),
    )

    def _duo_client_kwargs(self) -> dict:
        """Extra kwargs for the Duo client, carrying a custom CA chain if configured.

        `duo_client` accepts `ca_certs` only as a *path* to a PEM bundle, while authentik keeps
        certificates in the database. So the chain is materialised to a file, the same way
        `authentik.sources.ldap.models.LDAPSource.server()` does for `ldap3`.

        The file holds only the CA chain — public certificate material, never a private key —
        and is still written 0600 and into a private directory, so it is not readable by other
        users on the host.
        """
        if not self.ca_chain:
            return {}
        temp_dir = mkdtemp()
        with NamedTemporaryFile(mode="w", delete=False, dir=temp_dir, suffix=".pem") as temp_ca:
            temp_ca.write(self.ca_chain.certificate_data)
            ca_path = temp_ca.name
        chmod(ca_path, 0o600)
        return {"ca_certs": ca_path}

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_duo.api import AuthenticatorDuoStageSerializer

        return AuthenticatorDuoStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.authenticator_duo.stage import AuthenticatorDuoStageView

        return AuthenticatorDuoStageView

    def auth_client(self) -> Auth:
        """Get an API Client to talk to duo"""
        return Auth(
            self.client_id,
            self.client_secret,
            self.api_hostname,
            user_agent=authentik_user_agent(),
            **self._duo_client_kwargs(),
        )

    def admin_client(self) -> Admin:
        """Get an API Client to talk to duo"""
        if self.admin_integration_key == "" or self.admin_secret_key == "":  # nosec
            raise ValueError("Admin credentials not configured")
        client = Admin(
            self.admin_integration_key,
            self.admin_secret_key,
            self.api_hostname,
            user_agent=authentik_user_agent(),
            **self._duo_client_kwargs(),
        )
        return client

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-duo-form"

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-duo",
            }
        )

    def __str__(self) -> str:
        return f"Duo Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("Duo Authenticator Setup Stage")
        verbose_name_plural = _("Duo Authenticator Setup Stages")


class DuoDevice(SerializerModel, Device):
    """Duo Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorDuoStage, on_delete=models.PROTECT)
    duo_user_id = models.TextField()
    last_t = models.DateTimeField(auto_now=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_duo.api import DuoDeviceSerializer

        return DuoDeviceSerializer

    def __str__(self):
        return str(self.name) or str(self.user_id)

    class Meta:
        verbose_name = _("Duo Device")
        verbose_name_plural = _("Duo Devices")
