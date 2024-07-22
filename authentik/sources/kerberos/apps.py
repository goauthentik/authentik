"""authentik kerberos source config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceKerberosConfig(ManagedAppConfig):
    """Authentik source kerberos app config"""

    name = "authentik.sources.kerberos"
    label = "authentik_sources_kerberos"
    verbose_name = "authentik Sources.Kerberos"
    default = True
