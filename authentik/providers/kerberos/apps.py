"""authentik kerberos provider app config"""
from django.apps import AppConfig


class AuthentikProviderKerberosConfig(AppConfig):
    """authentik kerberos provider app config"""

    name = "authentik.providers.kerberos"
    label = "authentik_providers_kerberos"
    verbose_name = "authentik Providers.Kerberos"
    mountpoints = {
        "authentik.providers.kerberos.urls": "application/k/",
    }
