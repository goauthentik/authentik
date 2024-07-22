"""authentik Kerberos Source Models"""
import pglock
import os
from pathlib import Path
from tempfile import gettempdir
from typing import Any

import gssapi
import kadmin
from django.db import connection, models
from django.db.models.fields import b64decode
from django.http import HttpRequest
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import USER_PATH_SERVICE_ACCOUNT, PropertyMapping, Source, UserSourceConnection, UserTypes
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import RedirectChallenge

LOGGER = get_logger()


class KerberosSource(Source):
    """Federate Kerberos realm with authentik"""

    # python-kadmin leaks file descriptors. As such, this class attribute is used to re-use
    # existing kadmin connections instead of creating new ones, which results in less to no file
    # descriptors leaks
    _kadmin_connections: dict[str, Any] = {}

    realm = models.TextField(help_text=_("Kerberos realm"), unique=True)
    krb5_conf = models.TextField(
        blank=True,
        help_text=_("Custom krb5.conf to use. Uses the system one by default"),
    )

    sync_users = models.BooleanField(
        default=False, help_text=_("Sync users from Kerberos into authentik"), db_index=True
    )
    sync_users_password = models.BooleanField(
        default=True,
        help_text=_("When a user changes their password, sync it back to Kerberos"),
        db_index=True,
    )
    sync_principal = models.TextField(
        help_text=_("Principal to authenticate to kadmin for sync."), blank=True
    )
    sync_password = models.TextField(
        help_text=_("Password to authenticate to kadmin for sync"), blank=True
    )
    sync_keytab = models.TextField(
        help_text=_(
            (
                "Keytab to authenticate to kadmin for sync. "
                "Must be base64-encoded or in the form TYPE:residual"
            )
        ),
        blank=True,
    )
    sync_ccache = models.TextField(
        help_text=_(
            (
                "Credentials cache to authenticate to kadmin for sync. "
                "Must be in the form TYPE:residual"
            )
        ),
        blank=True,
    )

    spnego_server_name = models.TextField(
        help_text=_("Force the use of a specific server name for SPNEGO"),
        blank=True,
    )

    spnego_keytab = models.TextField(
        help_text=_("SPNEGO keytab base64-encoded or path to keytab in the form FILE:path"),
        blank=True,
    )
    spnego_ccache = models.TextField(
        help_text=_("Credential cache to use for SPNEGO in form type:residual"),
        blank=True,
    )

    password_login_enabled = models.BooleanField(
        default=False, help_text=_("Enable the passwword authentication backend"), db_index=True
    )
    password_login_update_internal_password = models.BooleanField(
        default=False,
        help_text=_(
            (
                "If enabled, the authentik-stored password will be updated upon "
                "login with the Kerberos password backend"
            )
        ),
    )

    class Meta:
        verbose_name = _("Kerberos Source")
        verbose_name_plural = _("Kerberos Sources")

    def __str__(self):
        return f"Kerberos Source {self.name}"

    @property
    def component(self) -> str:
        return "ak-source-kerberos-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.kerberos.api.source import KerberosSourceSerializer

        return KerberosSourceSerializer

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=RedirectChallenge(
                instance={
                    "to": reverse(
                        "authentik_sources_kerberos:login",
                        kwargs={"source_slug": self.slug},
                    ),
                }
            ),
            name=self.name,
            icon_url=self.icon_url,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        icon = self.icon_url
        if not icon:
            icon = static(f"authentik/sources/{self.slug}.svg")
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-kerberos",
                "configure_url": reverse(
                    "authentik_sources_kerberos:login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": icon,
            }
        )

    @property
    def sync_lock(self) -> pglock.advisory:
        """Redis lock for syncing Kerberos to prevent multiple parallel syncs happening"""
        return pglock.advisory(
            lock_id=f"goauthentik.io/{connection.schema_name}/sources/kerberos/sync/{self.slug}",
            timeout=0,
            side_effect=pglock.Return,
        )

    def get_base_user_properties(self, principal: str, **kwargs):
        localpart, realm = principal.rsplit("@", 1)
        is_service_account = "/" in localpart
        username = localpart

        # By default, don't sync system principals
        denied_prefixes = ["kadmin/", "krbtgt/", "K/M", "WELLKNOWN/"]
        for prefix in denied_prefixes:
            if username.lower().startswith(prefix.lower()):
                username = None
                break
        # By default, don't sync principals from another realm
        if realm.lower() != self.realm.lower():
            username = None

        properties = {
            "username": username,
            "type": UserTypes.INTERNAL,
            "path": self.get_user_path(),
        }
        if is_service_account:
            properties.update(
                {
                    "type": UserTypes.SERVICE_ACCOUNT,
                    "path": USER_PATH_SERVICE_ACCOUNT,
                }
            )
        return properties

    @property
    def tempdir(self) -> Path:
        """Get temporary storage for Kerberos files"""
        path = Path(gettempdir()) / "authentik" / connection.schema_name / "sources" / "kerberos" / str(self.pk)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return path

    @property
    def krb5_conf_path(self) -> str | None:
        """Get krb5.conf path"""
        if not self.krb5_conf:
            return None
        conf_path = self.tempdir / "krb5.conf"
        conf_path.write_text(self.krb5_conf)
        return str(conf_path)

    def _kadmin_init(self) -> "kadmin.KAdmin | None":
        # kadmin doesn't use a ccache for its connection
        # as such, we don't need to create a separate ccache for each source
        if not self.sync_principal:
            return None
        if self.sync_password:
            return kadmin.init_with_password(
                self.sync_principal,
                self.sync_password,
            )
        if self.sync_keytab:
            keytab = self.sync_keytab
            if ":" not in keytab:
                keytab_path = self.tempdir / "kadmin_keytab"
                keytab_path.touch(mode=0o600)
                keytab_path.write_bytes(b64decode(self.keytab))
                keytab = f"FILE:{keytab_path}"
            return kadmin.init_with_keytab(
                self.sync_principal,
                keytab,
            )
        if self.sync_ccache:
            return kadmin.init_with_ccache(
                self.sync_principal,
                self.sync_ccache,
            )
        return None

    def connection(self) -> "kadmin.KAdmin | None":
        """Get kadmin connection"""
        if str(self.pk) not in self._kadmin_connections:
            kadm = self._kadmin_init()
            if kadm is not None:
                self._kadmin_connections[str(self.pk)] = self._kadmin_init()
        return self._kadmin_connections.get(str(self.pk), None)

    def check_connection(self) -> dict[str, str]:
        """Check Kerberos Connection"""
        status = {"status": "ok"}
        if not self.sync_users:
            return status
        with Krb5ConfContext(self):
            try:
                kadm = self.connection()
                if kadm is None:
                    status["status"] = "no connection"
                    return status
                status["principal_exists"] = kadm.principal_exists(self.sync_principal)
            except kadmin.Error as exc:
                status["status"] = str(exc)
        return status

    def get_gssapi_store(self) -> dict[str, str]:
        """Get GSSAPI credentials store for this source"""
        ccache = self.spnego_ccache
        keytab = None

        if not ccache:
            ccache_path = self.tempdir / "spnego_ccache"
            ccache_path.touch(mode=0o600)
            ccache = f"FILE:{ccache_path}"

        if self.spnego_keytab:
            # Keytab is of the form type:residual, use as-is
            if ":" in self.spnego_keytab:
                keytab = self.spnego_keytab
            # Parse the keytab and write it in the file
            else:
                keytab_path = self.tempdir / "spnego_keytab"
                keytab_path.touch(mode=0o600)
                keytab_path.write_bytes(b64decode(self.spnego_keytab))
                keytab = f"FILE:{keytab_path}"

        store = {"ccache": ccache}
        if keytab is not None:
            store["keytab"] = keytab
        return store

    def get_gssapi_creds(self) -> gssapi.creds.Credentials | None:
        """Get GSSAPI credentials for this source"""
        try:
            name = None
            if self.spnego_server_name:
                # pylint: disable=c-extension-no-member
                name = gssapi.names.Name(
                    base=self.spnego_server_name,
                    name_type=gssapi.raw.types.NameType.hostbased_service,
                )
            return gssapi.creds.Credentials(
                usage="accept", name=name, store=self.get_gssapi_store()
            )
        except gssapi.exceptions.GSSError as exc:
            LOGGER.warn("GSSAPI credentials failure", exc=exc)
            return None


class Krb5ConfContext:
    """
    Context manager to set the path to the krb5.conf config file.
    """

    def __init__(self, source: KerberosSource):
        self._source = source
        self._path = self._source.krb5_conf_path
        self._previous = None

    def __enter__(self):
        if not self._path:
            return
        self._previous = os.environ.get("KRB5_CONFIG", None)
        os.environ["KRB5_CONFIG"] = self._path

    def __exit__(self, *args, **kwargs):
        if not self._path:
            return
        if self._previous:
            os.environ["KRB5_CONFIG"] = self._previous
        else:
            del os.environ["KRB5_CONFIG"]


class UserKerberosSourceConnection(UserSourceConnection):
    """Connection to configured Kerberos Sources."""

    identifier = models.TextField(db_index=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.sources.kerberos.api.source_connection import (
            UserKerberosSourceConnectionSerializer,
        )

        return UserKerberosSourceConnectionSerializer

    class Meta:
        verbose_name = _("User Kerberos Source Connection")
        verbose_name_plural = _("User Kerberos Source Connections")


class KerberosPropertyMapping(PropertyMapping):
    """Map Kerberos Property to User object attribute"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-kerberos-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.kerberos.api.property_mapping import (
            KerberosPropertyMappingSerializer,
        )

        return KerberosPropertyMappingSerializer

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Kerberos Property Mapping")
        verbose_name_plural = _("Kerberos Property Mapping")
