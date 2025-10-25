"""Authentik policy geoip app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyGeoIPConfig(ManagedAppConfig):
    """Authentik policy_geoip app config"""

    name = "authentik.policies.geoip"
    label = "authentik_policies_geoip"
    verbose_name = "authentik Policies.GeoIP"
    default = True
