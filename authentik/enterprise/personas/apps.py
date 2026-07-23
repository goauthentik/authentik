from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterprisePersonasConfig(EnterpriseConfig):
    name = "authentik.enterprise.personas"
    label = "authentik_personas"
    verbose_name = "authentik Enterprise.Personas"
    default = True
