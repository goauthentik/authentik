"""authentik tenant app"""
from django.apps import AppConfig


class AuthentikTenantsConfig(AppConfig):
    """authentik Tenant app"""

    name = "authentik.tenants"
    label = "authentik_tenants"
    verbose_name = "authentik Tenants"
