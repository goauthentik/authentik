"""Authentik policy geoip app config"""

from django.apps import AppConfig


class AuthentikPolicyGeoIPConfig(AppConfig):
    """Authentik policy_geoip app config"""

    name = "authentik.policies.geoip"
    label = "authentik_policies_geoip"
    verbose_name = "authentik Policies.GeoIP"
