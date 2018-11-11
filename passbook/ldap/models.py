# """Supervisr mod_ldap Models"""

# from django.contrib.auth.models import Group
# from django.db import models

# from supervisr.core.fields import JSONField
# from passbook.core.models import (CreatedUpdatedModel, ProductExtension,
#                                    UUIDModel)


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
