from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.api.v3.config import Capabilities, capabilities
from authentik.enterprise.agents.models import Agent, AgentPolicyTarget


@receiver(capabilities)
def agent_capabilities(sender, *_, request: HttpRequest, **__):
    if request.user.is_authenticated and request.user.has_perm(
        "authentik_agents.add_agent_self_service"
    ):
        return Capabilities.CAN_AGENT_SELF_SERVICE
    return None


@receiver(post_save, sender=Agent)
def agent_policy_target(sender, instance: Agent, **_):
    """Give every system agent a target to bind its ID-JAG policies to"""
    if instance.parent_id is None:
        AgentPolicyTarget.objects.get_or_create(agent=instance)
