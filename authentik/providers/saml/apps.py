"""authentik SAML IdP app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderSAMLConfig(ManagedAppConfig):
    """authentik SAML IdP app config"""

    name = "authentik.providers.saml"
    label = "authentik_providers_saml"
    verbose_name = "authentik Providers.SAML"
    mountpoint = "application/saml/"
    default = True
