"""passbook LDAP Models"""
from typing import Optional

from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from ldap3 import Connection, Server

from passbook.core.models import Group, PropertyMapping, Source


class LDAPSource(Source):
    """Federate LDAP Directory with passbook, or create new accounts in LDAP."""

    server_uri = models.TextField(
        validators=[URLValidator(schemes=["ldap", "ldaps"])],
        verbose_name=_("Server URI"),
    )
    bind_cn = models.TextField(verbose_name=_("Bind CN"))
    bind_password = models.TextField()
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
        default="(objectCategory=Person)",
        help_text=_("Consider Objects matching this filter to be Users."),
    )
    user_group_membership_field = models.TextField(
        default="memberOf", help_text=_("Field which contains Groups of user.")
    )
    group_object_filter = models.TextField(
        default="(objectCategory=Group)",
        help_text=_("Consider Objects matching this filter to be Groups."),
    )
    object_uniqueness_field = models.TextField(
        default="objectSid", help_text=_("Field which contains a unique Identifier.")
    )

    sync_users = models.BooleanField(default=True)
    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(
        Group, blank=True, null=True, default=None, on_delete=models.SET_DEFAULT
    )

    form = "passbook.sources.ldap.forms.LDAPSourceForm"

    _connection: Optional[Connection] = None

    @property
    def connection(self) -> Connection:
        """Get a fully connected and bound LDAP Connection"""
        if not self._connection:
            server = Server(self.server_uri)
            self._connection = Connection(
                server,
                raise_exceptions=True,
                user=self.bind_cn,
                password=self.bind_password,
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

    form = "passbook.sources.ldap.forms.LDAPPropertyMappingForm"

    def __str__(self):
        return f"LDAP Property Mapping {self.expression} -> {self.object_field}"

    class Meta:

        verbose_name = _("LDAP Property Mapping")
        verbose_name_plural = _("LDAP Property Mappings")
