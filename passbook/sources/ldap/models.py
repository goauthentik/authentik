"""passbook LDAP Models"""

from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Group, PropertyMapping, Source


class LDAPSource(Source):
    """LDAP Authentication source"""

    server_uri = models.TextField(validators=[URLValidator(schemes=['ldap', 'ldaps'])])
    bind_cn = models.TextField()
    bind_password = models.TextField()
    start_tls = models.BooleanField(default=False)

    base_dn = models.TextField()
    additional_user_dn = models.TextField(help_text=_('Prepended to Base DN for User-queries.'))
    additional_group_dn = models.TextField(help_text=_('Prepended to Base DN for Group-queries.'))

    user_object_filter = models.TextField(default="(objectCategory=Person)", help_text=_(
        'Consider Objects matching this filter to be Users.'))
    user_group_membership_field = models.TextField(default="memberOf", help_text=_(
        "Field which contains Groups of user."))
    group_object_filter = models.TextField(default="(objectCategory=Group)", help_text=_(
        'Consider Objects matching this filter to be Groups.'))
    object_uniqueness_field = models.TextField(default="objectSid", help_text=_(
        'Field which contains a unique Identifier.'))

    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(Group, blank=True, null=True,
                                          default=None, on_delete=models.SET_DEFAULT)

    form = 'passbook.sources.ldap.forms.LDAPSourceForm'

    class Meta:

        verbose_name = _('LDAP Source')
        verbose_name_plural = _('LDAP Sources')


class LDAPPropertyMapping(PropertyMapping):
    """Map LDAP Property to User or Group object"""

    ldap_property = models.TextField()
    object_field = models.TextField()

    form = 'passbook.sources.ldap.forms.LDAPPropertyMappingForm'

    def __str__(self):
        return f"LDAP Property Mapping {self.ldap_property} -> {self.object_field}"

    class Meta:

        verbose_name = _('LDAP Property Mapping')
        verbose_name_plural = _('LDAP Property Mappings')
