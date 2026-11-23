from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseAgentsConfig(EnterpriseConfig):
    name = "authentik.enterprise.agents"
    label = "authentik_agents"
    verbose_name = "authentik Enterprise.Agents"
    default = True
