"""passbook LDAP Models"""

from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Group, PropertyMapping, Source


class LDAPSource(Source):
    """LDAP Authentication source"""

    server_uri = models.URLField(validators=[URLValidator(schemes=['ldap', 'ldaps'])])
    bind_cn = models.TextField()
    bind_password = models.TextField()
    start_tls = models.BooleanField(default=False)

    base_dn = models.TextField()
    additional_user_dn = models.TextField(help_text=_('Prepended to Base DN for User-queries.'))
    additional_group_dn = models.TextField(help_text=_('Prepended to Base DN for Group-queries.'))

    user_object_filter = models.TextField()
    group_object_filter = models.TextField()

    sync_groups = models.BooleanField(default=True)
    sync_parent_group = models.ForeignKey(Group, blank=True,
                                          default=None, on_delete=models.SET_DEFAULT)

    form = 'passbook.sources.ldap.forms.LDAPSourceForm'

    @property
    def get_login_button(self):
        raise NotImplementedError()

    class Meta:

        verbose_name = _('LDAP Source')
        verbose_name_plural = _('LDAP Sources')


class LDAPPropertyMapping(PropertyMapping):

    ldap_property = models.TextField()
    object_field = models.TextField()
