from django.utils.translation import gettext_lazy as _

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
