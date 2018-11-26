"""passbook LDAP Models"""

from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Source


class LDAPSource(Source):
    """LDAP Authentication source"""

    TYPE_ACTIVE_DIRECTORY = 'ad'
    TYPE_GENERIC = 'generic'
    TYPES = (
        (TYPE_ACTIVE_DIRECTORY, TYPE_ACTIVE_DIRECTORY),
        (TYPE_GENERIC, TYPE_GENERIC),
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

    class Meta:

        verbose_name = _('LDAP Source')
        verbose_name_plural = _('LDAP Sources')


# class LDAPModification(UUIDModel, CreatedUpdatedModel):
#     """Store LDAP Data in DB if LDAP Server is unavailable"""
#     ACTION_ADD = 'ADD'
#     ACTION_MODIFY = 'MODIFY'

#     ACTIONS = (
#         (ACTION_ADD, 'ADD'),
#         (ACTION_MODIFY, 'MODIFY'),
#     )

#     dn = models.CharField(max_length=255)
#     action = models.CharField(max_length=17, choices=ACTIONS, default=ACTION_MODIFY)
#     data = JSONField()

#     def __str__(self):
#         return "LDAPModification %d from %s" % (self.pk, self.created)


# class LDAPGroupMapping(UUIDModel, CreatedUpdatedModel):
#     """Model to map an LDAP Group to a supervisr group"""

#     ldap_dn = models.TextField()
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)

#     def __str__(self):
#         return "LDAPGroupMapping %s -> %s" % (self.ldap_dn, self.group.name)
