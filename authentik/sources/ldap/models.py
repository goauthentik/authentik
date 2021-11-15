"""authentik LDAP Models"""
from typing import Optional, Type

from django.db import models
from django.utils.translation import gettext_lazy as _
from ldap3 import ALL, Connection, Server
from rest_framework.serializers import Serializer

from authentik.core.models import Group, PropertyMapping, Source
from authentik.lib.models import DomainlessURLValidator

LDAP_TIMEOUT = 15


class LDAPSource(Source):
    """Federate LDAP Directory with authentik, or create new accounts in LDAP."""

    server_uri = models.TextField(
        validators=[DomainlessURLValidator(schemes=["ldap", "ldaps"])],
        verbose_name=_("Server URI"),
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
    def serializer(self) -> Type[Serializer]:
        from authentik.sources.ldap.api import LDAPSourceSerializer

        return LDAPSourceSerializer

    _connection: Optional[Connection] = None

    @property
    def connection(self) -> Connection:
        """Get a fully connected and bound LDAP Connection"""
        if not self._connection:
            server = Server(self.server_uri, get_info=ALL, connect_timeout=LDAP_TIMEOUT)
            self._connection = Connection(
                server,
                raise_exceptions=True,
                user=self.bind_cn,
                password=self.bind_password,
                receive_timeout=LDAP_TIMEOUT,
            )

            self._connection.bind()
            if self.start_tls:
                self._connection.start_tls()
        return self._connection

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
    def serializer(self) -> Type[Serializer]:
        from authentik.sources.ldap.api import LDAPPropertyMappingSerializer

        return LDAPPropertyMappingSerializer

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("LDAP Property Mapping")
        verbose_name_plural = _("LDAP Property Mappings")
