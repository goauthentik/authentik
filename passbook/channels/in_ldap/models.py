"""passbook LDAP Models"""

from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Group, Inlet, PropertyMapping


class LDAPInlet(Inlet):
    """LDAP Authentication inlet"""

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
    )
    additional_group_dn = models.TextField(
        help_text=_("Prepended to Base DN for Group-queries."),
        verbose_name=_("Addition Group DN"),
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

    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(
        Group, blank=True, null=True, default=None, on_delete=models.SET_DEFAULT
    )

    form = "passbook.channels.in_ldap.forms.LDAPInletForm"

    class Meta:

        verbose_name = _("LDAP Inlet")
        verbose_name_plural = _("LDAP Inlets")


class LDAPPropertyMapping(PropertyMapping):
    """Map LDAP Property to User or Group object"""

    object_field = models.TextField()

    form = "passbook.channels.in_ldap.forms.LDAPPropertyMappingForm"

    def __str__(self):
        return f"LDAP Property Mapping {self.expression} -> {self.object_field}"

    class Meta:

        verbose_name = _("LDAP Property Mapping")
        verbose_name_plural = _("LDAP Property Mappings")
