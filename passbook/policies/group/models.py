"""passbook group models models"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Group, Policy
from passbook.policies.struct import PolicyRequest, PolicyResult


class GroupMembershipPolicy(Policy):
    """Policy to check if the user is member in a certain group"""

    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    form = 'passbook.policies.group.forms.GroupMembershipPolicyForm'

    def passes(self, request: PolicyRequest) -> PolicyResult:
        return PolicyResult(self.group.user_set.filter(pk=request.user.pk).exists())

    class Meta:

        verbose_name = _('Group Membership Policy')
        verbose_name_plural = _('Group Membership Policies')
