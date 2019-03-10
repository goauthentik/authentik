"""passbook LDAP Models"""

from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Policy, Source, User


class LDAPSource(Source):
    """LDAP Authentication source"""

    TYPE_ACTIVE_DIRECTORY = 'ad'
    TYPE_GENERIC = 'generic'
    TYPES = (
        (TYPE_ACTIVE_DIRECTORY, _('Active Directory')),
        (TYPE_GENERIC, _('Generic')),
    )

    server_uri = models.TextField()
    bind_cn = models.TextField()
    bind_password = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)

    domain = models.TextField()
    base_dn = models.TextField()
    create_user = models.BooleanField(default=False)
    reset_password = models.BooleanField(default=True)

    form = 'passbook.ldap.forms.LDAPSourceForm'

    @property
    def get_login_button(self):
        raise NotImplementedError()

    class Meta:

        verbose_name = _('LDAP Source')
        verbose_name_plural = _('LDAP Sources')

class LDAPGroupMembershipPolicy(Policy):
    """Policy to check if a user is in a certain LDAP Group"""

    dn = models.TextField()
    source = models.ForeignKey('LDAPSource', on_delete=models.CASCADE)

    form = 'passbook.ldap.forms.LDAPGroupMembershipPolicyForm'

    def passes(self, user: User):
        """Check if user instance passes this policy"""
        raise NotImplementedError()

    class Meta:

        verbose_name = _('LDAP Group Membership Policy')
        verbose_name_plural = _('LDAP Group Membership Policys')
