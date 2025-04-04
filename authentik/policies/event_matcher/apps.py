"""authentik Event Matcher policy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPoliciesEventMatcherConfig(ManagedAppConfig):
    """authentik Event Matcher policy app config"""

    name = "authentik.policies.event_matcher"
    label = "authentik_policies_event_matcher"
    verbose_name = "authentik Policies.Event Matcher"
    default = True
