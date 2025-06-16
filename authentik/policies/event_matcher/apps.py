"""authentik Event Matcher policy app config"""

from django.apps import AppConfig


class AuthentikPoliciesEventMatcherConfig(AppConfig):
    """authentik Event Matcher policy app config"""

    name = "authentik.policies.event_matcher"
    label = "authentik_policies_event_matcher"
    verbose_name = "authentik Policies.Event Matcher"
