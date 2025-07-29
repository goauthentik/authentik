"""authentik LDAP Models"""

from os import chmod
from os.path import dirname, exists
from shutil import rmtree
from ssl import CERT_REQUIRED
from tempfile import NamedTemporaryFile, mkdtemp
from typing import Any

import pglock
from django.db import connection, models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from ldap3 import ALL, NONE, RANDOM, Connection, Server, ServerPool, Tls
from ldap3.core.exceptions import LDAPException, LDAPInsufficientAccessRightsResult, LDAPSchemaError
from rest_framework.serializers import Serializer

from authentik.core.models import (
    Group,
    GroupSourceConnection,
    PropertyMapping,
    Source,
    UserSourceConnection,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.config import CONFIG
from authentik.lib.models import DomainlessURLValidator
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import ScheduledModel

LDAP_TIMEOUT = 15
LDAP_UNIQUENESS = "ldap_uniq"
LDAP_DISTINGUISHED_NAME = "distinguishedName"


def flatten(value: Any) -> Any:
    """Flatten `value` if its a list, set or tuple"""
    if isinstance(value, list | set | tuple):
        if len(value) < 1:
            return None
        if isinstance(value, set):
            return value.pop()
        return value[0]
    return value


class MultiURLValidator(DomainlessURLValidator):
    """Same as DomainlessURLValidator but supports multiple URLs separated with a comma."""

    def __call__(self, value: str):
        if "," in value:
            for url in value.split(","):
                super().__call__(url)
        else:
            super().__call__(value)


class LDAPSource(ScheduledModel, Source):
    """Federate LDAP Directory with authentik, or create new accounts in LDAP."""

    server_uri = models.TextField(
        validators=[MultiURLValidator(schemes=["ldap", "ldaps"])],
        verbose_name=_("Server URI"),
    )
    peer_certificate = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="ldap_peer_certificates",
        help_text=_(
            "Optionally verify the LDAP Server's Certificate against the CA Chain in this keypair."
        ),
    )
    client_certificate = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="ldap_client_certificates",
        help_text=_("Client certificate to authenticate against the LDAP Server's Certificate."),
    )

    bind_cn = models.TextField(verbose_name=_("Bind CN"), blank=True)
    bind_password = models.TextField(blank=True)
    start_tls = models.BooleanField(default=False, verbose_name=_("Enable Start TLS"))
    sni = models.BooleanField(default=False, verbose_name=_("Use Server URI for SNI verification"))

    base_dn = models.TextField(verbose_name=_("Base DN"))
    additional_user_dn = models.TextField(
        help_text=_("Prepended to Base DN for User-queries."),
        verbose_name=_("Addition User DN"),
        blank=True,
    )
    additional_group_dn = models.TextField(
        help_text=_("Prepended to Base DN for Group-queries."),
        verbose_name=_("Addition Group DN"),
        blank=True,
    )

    user_object_filter = models.TextField(
        default="(objectClass=person)",
        help_text=_("Consider Objects matching this filter to be Users."),
    )
    user_membership_attribute = models.TextField(
        default=LDAP_DISTINGUISHED_NAME,
        help_text=_("Attribute which matches the value of `group_membership_field`."),
    )
    group_membership_field = models.TextField(
        default="member", help_text=_("Field which contains members of a group.")
    )
    group_object_filter = models.TextField(
        default="(objectClass=group)",
        help_text=_("Consider Objects matching this filter to be Groups."),
    )
    object_uniqueness_field = models.TextField(
        default="objectSid", help_text=_("Field which contains a unique Identifier.")
    )

    password_login_update_internal_password = models.BooleanField(
        default=False,
        help_text=_("Update internal authentik password when login succeeds with LDAP"),
    )

    sync_users = models.BooleanField(default=True)
    sync_users_password = models.BooleanField(
        default=True,
        help_text=_(
            "When a user changes their password, sync it back to LDAP. "
            "This can only be enabled on a single LDAP source."
        ),
    )
    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(
        Group, blank=True, null=True, default=None, on_delete=models.SET_DEFAULT
    )

    lookup_groups_from_user = models.BooleanField(
        default=False,
        help_text=_(
            "Lookup group membership based on a user attribute instead of a group attribute. "
            "This allows nested group resolution on systems like FreeIPA and Active Directory"
        ),
    )

    delete_not_found_objects = models.BooleanField(
        default=False,
        help_text=_(
            "Delete authentik users and groups which were previously supplied by this source, "
            "but are now missing from it."
        ),
    )

    @property
    def component(self) -> str:
        return "ak-source-ldap-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import LDAPSourceSerializer

        return LDAPSourceSerializer

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.sources.ldap.tasks import ldap_connectivity_check, ldap_sync

        return [
            ScheduleSpec(
                actor=ldap_sync,
                uid=self.slug,
                args=(self.pk,),
                crontab=f"{fqdn_rand('ldap_sync/' + str(self.pk))} */2 * * *",
                send_on_save=True,
            ),
            ScheduleSpec(
                actor=ldap_connectivity_check,
                uid=self.slug,
                args=(self.pk,),
                crontab=f"{fqdn_rand('ldap_connectivity_check/' + str(self.pk))} * * * *",
                send_on_save=True,
            ),
        ]

    @property
    def property_mapping_type(self) -> "type[PropertyMapping]":
        from authentik.sources.ldap.models import LDAPSourcePropertyMapping

        return LDAPSourcePropertyMapping

    def update_properties_with_uniqueness_field(self, properties, dn, ldap, **kwargs):
        properties.setdefault("attributes", {})[LDAP_DISTINGUISHED_NAME] = dn
        if self.object_uniqueness_field in ldap:
            properties["attributes"][LDAP_UNIQUENESS] = flatten(
                ldap.get(self.object_uniqueness_field)
            )
        return properties

    def get_base_user_properties(self, **kwargs):
        return self.update_properties_with_uniqueness_field({}, **kwargs)

    def get_base_group_properties(self, **kwargs):
        return self.update_properties_with_uniqueness_field(
            {
                "parent": self.sync_parent_group,
            },
            **kwargs,
        )

    @property
    def icon_url(self) -> str:
        return static("authentik/sources/ldap.png")

    def server(self, **kwargs) -> ServerPool:
        """Get LDAP Server/ServerPool"""
        servers = []
        tls_kwargs = {}
        if self.peer_certificate:
            tls_kwargs["ca_certs_data"] = self.peer_certificate.certificate_data
            tls_kwargs["validate"] = CERT_REQUIRED
        if self.client_certificate:
            temp_dir = mkdtemp()
            with NamedTemporaryFile(mode="w", delete=False, dir=temp_dir) as temp_cert:
                temp_cert.write(self.client_certificate.certificate_data)
                certificate_file = temp_cert.name
                chmod(certificate_file, 0o600)
            with NamedTemporaryFile(mode="w", delete=False, dir=temp_dir) as temp_key:
                temp_key.write(self.client_certificate.key_data)
                private_key_file = temp_key.name
                chmod(private_key_file, 0o600)
            tls_kwargs["local_private_key_file"] = private_key_file
            tls_kwargs["local_certificate_file"] = certificate_file
        if ciphers := CONFIG.get("ldap.tls.ciphers", None):
            tls_kwargs["ciphers"] = ciphers.strip()
        if self.sni:
            tls_kwargs["sni"] = self.server_uri.split(",", maxsplit=1)[0].strip()
        server_kwargs = {
            "get_info": ALL,
            "connect_timeout": LDAP_TIMEOUT,
            "tls": Tls(**tls_kwargs),
        }
        server_kwargs.update(kwargs)
        if "," in self.server_uri:
            for server in self.server_uri.split(","):
                servers.append(Server(server, **server_kwargs))
        else:
            servers = [Server(self.server_uri, **server_kwargs)]
        return ServerPool(servers, RANDOM, active=5, exhaust=True)

    def connection(
        self,
        server: Server | None = None,
        server_kwargs: dict | None = None,
        connection_kwargs: dict | None = None,
    ) -> Connection:
        """Get a fully connected and bound LDAP Connection"""
        server_kwargs = server_kwargs or {}
        connection_kwargs = connection_kwargs or {}
        if self.bind_cn is not None:
            connection_kwargs.setdefault("user", self.bind_cn)
        if self.bind_password is not None:
            connection_kwargs.setdefault("password", self.bind_password)
        conn = Connection(
            server or self.server(**server_kwargs),
            raise_exceptions=True,
            receive_timeout=LDAP_TIMEOUT,
            **connection_kwargs,
        )

        if self.start_tls:
            conn.start_tls(read_server_info=False)
        try:
            successful = conn.bind()
            if successful:
                return conn
        except (LDAPSchemaError, LDAPInsufficientAccessRightsResult) as exc:
            # Schema error, so try connecting without schema info
            # See https://github.com/goauthentik/authentik/issues/4590
            # See also https://github.com/goauthentik/authentik/issues/3399
            if server_kwargs.get("get_info", ALL) == NONE:
                raise exc
            server_kwargs["get_info"] = NONE
            return self.connection(server, server_kwargs, connection_kwargs)
        finally:
            if conn.server.tls.certificate_file is not None and exists(
                conn.server.tls.certificate_file
            ):
                rmtree(dirname(conn.server.tls.certificate_file))
        return RuntimeError("Failed to bind")

    @property
    def sync_lock(self) -> pglock.advisory:
        """Postgres lock for syncing LDAP to prevent multiple parallel syncs happening"""
        return pglock.advisory(
            lock_id=f"goauthentik.io/{connection.schema_name}/sources/ldap/sync/{self.slug}",
            timeout=0,
            side_effect=pglock.Return,
        )

    def check_connection(self) -> dict[str, dict[str, str]]:
        """Check LDAP Connection"""
        servers = self.server()
        server_info = {}
        # Check each individual server
        for server in servers.servers:
            server: Server
            try:
                conn = self.connection(server=server)
                server_info[server.host] = {
                    "vendor": str(flatten(conn.server.info.vendor_name)),
                    "version": str(flatten(conn.server.info.vendor_version)),
                    "status": "ok",
                }
            except LDAPException as exc:
                server_info[server.host] = {
                    "status": str(exc),
                }
        # Check server pool
        try:
            conn = self.connection()
            server_info["__all__"] = {
                "vendor": str(flatten(conn.server.info.vendor_name)),
                "version": str(flatten(conn.server.info.vendor_version)),
                "status": "ok",
            }
        except LDAPException as exc:
            server_info["__all__"] = {
                "status": str(exc),
            }
        return server_info

    class Meta:
        verbose_name = _("LDAP Source")
        verbose_name_plural = _("LDAP Sources")


class LDAPSourcePropertyMapping(PropertyMapping):
    """Map LDAP Property to User or Group object attribute"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-ldap-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import LDAPSourcePropertyMappingSerializer

        return LDAPSourcePropertyMappingSerializer

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("LDAP Source Property Mapping")
        verbose_name_plural = _("LDAP Source Property Mappings")


class UserLDAPSourceConnection(UserSourceConnection):
    validated_by = models.UUIDField(
        null=True,
        blank=True,
        help_text=_("Unique ID used while checking if this object still exists in the directory."),
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import (
            UserLDAPSourceConnectionSerializer,
        )

        return UserLDAPSourceConnectionSerializer

    class Meta:
        verbose_name = _("User LDAP Source Connection")
        verbose_name_plural = _("User LDAP Source Connections")
        indexes = [
            models.Index(fields=["validated_by"]),
        ]


class GroupLDAPSourceConnection(GroupSourceConnection):
    validated_by = models.UUIDField(
        null=True,
        blank=True,
        help_text=_("Unique ID used while checking if this object still exists in the directory."),
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import (
            GroupLDAPSourceConnectionSerializer,
        )

        return GroupLDAPSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group LDAP Source Connection")
        verbose_name_plural = _("Group LDAP Source Connections")
        indexes = [
            models.Index(fields=["validated_by"]),
        ]
