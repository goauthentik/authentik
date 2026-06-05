from django.db import models

from authentik.core.models import Group, User
from authentik.policies.models import Policy


class AccessRequestPolicy(Policy):

    approver_groups = models.ManyToManyField(Group)
    approver_users = models.ManyToManyField(User)


