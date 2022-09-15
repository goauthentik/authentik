"""authentik LDAP Models"""
from ssl import CERT_REQUIRED

from django.db import models
from django.utils.translation import gettext_lazy as _
from ldap3 import ALL, RANDOM, Connection, Server, ServerPool, Tls
from rest_framework.serializers import Serializer

from authentik.core.models import Group, PropertyMapping, Source
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.config import CONFIG
from authentik.lib.models import DomainlessURLValidator

LDAP_TIMEOUT = 15


class MultiURLValidator(DomainlessURLValidator):
    """Same as DomainlessURLValidator but supports multiple URLs separated with a comma."""

    def __call__(self, value: str):
        if "," in value:
            for url in value.split(","):
                super().__call__(url)
        else:
            super().__call__(value)


class LDAPSource(Source):
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
        help_text=_(
            "Optionally verify the LDAP Server's Certificate "
            "against the CA Chain in this keypair."
        ),
    )

    bind_cn = models.TextField(verbose_name=_("Bind CN"), blank=True)
    bind_password = models.TextField(blank=True)
    start_tls = models.BooleanField(default=False, verbose_name=_("Enable Start TLS"))

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

    property_mappings_group = models.ManyToManyField(
        PropertyMapping,
        default=None,
        blank=True,
        help_text=_("Property mappings used for group creation/updating."),
    )

    sync_users = models.BooleanField(default=True)
    sync_users_password = models.BooleanField(
        default=True,
        help_text=_(
            (
                "When a user changes their password, sync it back to LDAP. "
                "This can only be enabled on a single LDAP source."
            )
        ),
    )
    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(
        Group, blank=True, null=True, default=None, on_delete=models.SET_DEFAULT
    )

    @property
    def component(self) -> str:
        return "ak-source-ldap-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import LDAPSourceSerializer

        return LDAPSourceSerializer

    @property
    def server(self) -> Server:
        """Get LDAP Server/ServerPool"""
        servers = []
        tls_kwargs = {}
        if self.peer_certificate:
            tls_kwargs["ca_certs_data"] = self.peer_certificate.certificate_data
            tls_kwargs["validate"] = CERT_REQUIRED
        if ciphers := CONFIG.y("ldap.tls.ciphers", None):
            tls_kwargs["ciphers"] = ciphers.strip()
        kwargs = {
            "get_info": ALL,
            "connect_timeout": LDAP_TIMEOUT,
            "tls": Tls(**tls_kwargs),
        }
        if "," in self.server_uri:
            for server in self.server_uri.split(","):
                servers.append(Server(server, **kwargs))
        else:
            servers = [Server(self.server_uri, **kwargs)]
        return ServerPool(servers, RANDOM, active=True, exhaust=True)

    @property
    def connection(self) -> Connection:
        """Get a fully connected and bound LDAP Connection"""
        connection = Connection(
            self.server,
            raise_exceptions=True,
            user=self.bind_cn,
            password=self.bind_password,
            receive_timeout=LDAP_TIMEOUT,
        )

        if self.start_tls:
            connection.start_tls(read_server_info=False)
        connection.bind()
        return connection

    class Meta:

        verbose_name = _("LDAP Source")
        verbose_name_plural = _("LDAP Sources")


class LDAPPropertyMapping(PropertyMapping):
    """Map LDAP Property to User or Group object attribute"""

    object_field = models.TextField()

    @property
    def component(self) -> str:
        return "ak-property-mapping-ldap-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.ldap.api import LDAPPropertyMappingSerializer

        return LDAPPropertyMappingSerializer

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("LDAP Property Mapping")
        verbose_name_plural = _("LDAP Property Mappings")
