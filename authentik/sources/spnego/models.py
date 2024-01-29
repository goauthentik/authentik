"""SPNEGO source models"""
from base64 import b64decode
from pathlib import Path
from tempfile import gettempdir
from typing import Optional

import gssapi
from django.db import models
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import ChallengeTypes, RedirectChallenge

LOGGER = get_logger()


class SPNEGOSource(Source):
    """Authenticate using an external SPNEGO Identity Provider."""

    server_name = models.TextField(
        help_text=_("Force the use of a specific server name"),
        blank=True,
    )

    keytab = models.TextField(
        help_text=_("Keytab base64-encoded or path to keytab in the form FILE:path"),
        blank=True,
    )
    ccache = models.TextField(
        help_text=_("Credential cache to use in form type:residual"),
        blank=True,
    )

    guess_email = models.BooleanField(
        default=False, help_text=_("Guess user email based on their principal.")
    )

    @property
    def component(self) -> str:
        return "ak-source-spnego-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.spnego.api.source import SPNEGOSourceSerializer

        return SPNEGOSourceSerializer

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=RedirectChallenge(
                instance={
                    "type": ChallengeTypes.REDIRECT.value,
                    "to": reverse(
                        "authentik_sources_spnego:login",
                        kwargs={"source_slug": self.slug},
                    ),
                }
            ),
            name=self.name,
            icon_url=self.icon_url,
        )

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        icon = self.icon_url
        if not icon:
            icon = static(f"authentik/sources/{self.slug}.svg")
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-spnego",
                "configure_url": reverse(
                    "authentik_sources_spnego:login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": icon,
            }
        )

    def __str__(self):
        return f"SPNEGO Source {self.name}"

    class Meta:
        verbose_name = _("SPNEGO Source")
        verbose_name_plural = _("SPNEGO Sources")

    def get_gssapi_store(self) -> dict[str, str]:
        """Get GSSAPI credentials store for this source"""
        ccache = self.ccache
        keytab = None

        paths_prefix = Path(gettempdir()) / "authentik" / "sources" / "spnego" / str(self.pk)
        paths_prefix.mkdir(parents=True, exist_ok=True)

        if not ccache:
            ccache_path = paths_prefix / "ccache"
            ccache_path.touch()
            ccache = f"FILE:{ccache_path}"

        if self.keytab:
            # Keytab is of the form type:residual, use as-is
            if ":" in self.keytab:
                keytab = self.keytab
            # Parse the keytab and write it in the file
            else:
                keytab_path = paths_prefix / "keytab"
                keytab_path.write_bytes(b64decode(self.keytab))
                keytab = f"FILE:{keytab_path}"

        store = {"ccache": ccache}
        if keytab is not None:
            store["keytab"] = keytab
        return store

    def get_gssapi_creds(self) -> gssapi.creds.Credentials | None:
        """Get GSSAPI credentials for this source"""
        try:
            name = None
            if self.server_name:
                # pylint: disable=c-extension-no-member
                name = gssapi.names.Name(
                    base=self.server_name, name_type=gssapi.raw.types.NameType.hostbased_service
                )
            return gssapi.creds.Credentials(
                usage="accept", name=name, store=self.get_gssapi_store()
            )
        except gssapi.exceptions.GSSError as exc:
            LOGGER.warn("GSSAPI credentials failure", exc=exc)
            return None


class UserSPNEGOSourceConnection(UserSourceConnection):
    """Connection to configured SPNEGO Sources."""

    identifier = models.TextField()

    @property
    def serializer(self) -> Serializer:
        from authentik.sources.spnego.api.source_connection import (
            UserSPNEGOSourceConnectionSerializer,
        )

        return UserSPNEGOSourceConnectionSerializer

    class Meta:
        verbose_name = _("User SPNEGO Source Connection")
        verbose_name_plural = _("User SPNEGO Source Connections")
