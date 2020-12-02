"""authentik Group Membership policy app config"""

from django.apps import AppConfig


class AuthentikPoliciesGroupMembershipConfig(AppConfig):
    """authentik Group Membership policy app config"""

    name = "authentik.policies.group_membership"
    label = "authentik_policies_group_membership"
    verbose_name = "authentik Policies.Group Membership"
