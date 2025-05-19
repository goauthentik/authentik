"""authentik stage app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseStageMTLSConfig(EnterpriseConfig):
    """authentik MTLS stage config"""

    name = "authentik.enterprise.stages.mtls"
    label = "authentik_stages_mtls"
    verbose_name = "authentik Enterprise.Stages.MTLS"
    default = True
