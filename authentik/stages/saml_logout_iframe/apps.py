"""SAML iframe logout stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStagesSAMLLogoutIframeConfig(ManagedAppConfig):
    """SAML iframe logout stage app config"""

    name = "authentik.stages.saml_logout_iframe"
    label = "authentik_stages_saml_logout_iframe"
    verbose_name = "authentik Stages.SAML Logout Iframe"
    default = True
