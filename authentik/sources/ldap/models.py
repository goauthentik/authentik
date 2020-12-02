"""authentik LDAP Models"""
from datetime import datetime
from typing import Optional, Type

from django.core.cache import cache
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from ldap3 import ALL, Connection, Server

from authentik.core.models import Group, PropertyMapping, Source
from authentik.lib.models import DomainlessURLValidator
from authentik.lib.utils.template import render_to_string


class LDAPSource(Source):
    """Federate LDAP Directory with authentik, or create new accounts in LDAP."""

    server_uri = models.TextField(
        validators=[DomainlessURLValidator(schemes=["ldap", "ldaps"])],
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
    sync_users_password = models.BooleanField(
        default=True,
        help_text=_(
            (
                "When a user changes their password, sync it back to LDAP. "
                "This can only be enabled on a single LDAP source."
            )
        ),
        unique=True,
    )
    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(
        Group, blank=True, null=True, default=None, on_delete=models.SET_DEFAULT
    )

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.sources.ldap.forms import LDAPSourceForm

        return LDAPSourceForm

    def state_cache_prefix(self, suffix: str) -> str:
        """Key by which the ldap source status is saved"""
        return f"source_ldap_{self.pk}_state_{suffix}"

    @property
    def ui_additional_info(self) -> str:
        last_sync = cache.get(self.state_cache_prefix("last_sync"), None)
        if last_sync:
            last_sync = datetime.fromtimestamp(last_sync)

        return render_to_string(
            "ldap/source_list_status.html", {"source": self, "last_sync": last_sync}
        )

    _connection: Optional[Connection] = None

    @property
    def connection(self) -> Connection:
        """Get a fully connected and bound LDAP Connection"""
        if not self._connection:
            server = Server(self.server_uri, get_info=ALL)
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

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.sources.ldap.forms import LDAPPropertyMappingForm

        return LDAPPropertyMappingForm

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("LDAP Property Mapping")
        verbose_name_plural = _("LDAP Property Mappings")
