from django.utils.translation import gettext_lazy as _

from authentik.blueprints.apps import ManagedAppConfig
from authentik.enterprise.apps import EnterpriseConfig
from authentik.tenants.flags import Flag


class AllowAnyAgentCreate(Flag[bool], key="enterprise_agent_allow_any"):

    default = False
    visibility = "authenticated"
    description = _("When enabled, allow any user to create agent accounts.")


class AuthentikEnterpriseAgentsConfig(EnterpriseConfig):
    name = "authentik.enterprise.agents"
    label = "authentik_agents"
    verbose_name = "authentik Enterprise.Agents"
    default = True

    @ManagedAppConfig.reconcile_global
    def register_policy_check(self):
        """Register the agent application-scope check into the global policy engine."""
        from authentik.enterprise.agents.policies import agent_application_access
        from authentik.policies.engine import GLOBAL_POLICY_CHECKS

        if agent_application_access not in GLOBAL_POLICY_CHECKS:
            GLOBAL_POLICY_CHECKS.append(agent_application_access)
