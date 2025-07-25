"""authentik SAML Logout stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageSAMLLogoutConfig(ManagedAppConfig):
    """authentik SAML Logout stage app config"""

    name = "authentik.stages.saml_logout"
    label = "authentik_stages_saml_logout"
    verbose_name = "authentik Stages.SAML Logout"
    default = True
