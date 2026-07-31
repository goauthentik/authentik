from django.utils.translation import gettext_lazy as _

from authentik.core.models import (
    USER_PATH_SYSTEM_PREFIX,
    Actor,
    ActorPolicyInheritance,
    User,
    UserTypes,
)
from authentik.lib.generators import generate_id

USER_PATH_AGENTS = f"{USER_PATH_SYSTEM_PREFIX}/agents"


class Agent(Actor):

    class Meta:
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")

    @classmethod
    def create_for_user(
        cls,
        user: User,
        name: str = "",
        expiring: bool = False,
        expires=None,
        policy_behavior: str = ActorPolicyInheritance.MIRROR,
    ) -> Agent:
        # An agent is a machine identity, not a login user: mark it as a service account
        # and disable password auth. It authenticates through its issued API token. By default
        # it MIRRORs its parent, so it can never exceed the access of the user it acts for.
        agent = cls.objects.create(
            username=f"agent-{generate_id()}",
            name=name,
            parent=user,
            policy_behavior=policy_behavior,
            type=UserTypes.SERVICE_ACCOUNT,
            path=USER_PATH_AGENTS,
            expiring=expiring,
            expires=expires,
        )
        agent.set_unusable_password()
        agent.save()
        if policy_behavior == ActorPolicyInheritance.COPY:
            agent.copy_parent_policy_bindings()
        return agent

    @property
    def serializer(self):
        from authentik.enterprise.agents.api import AgentSerializer

        return AgentSerializer

    def __str__(self):
        return f"Agent {self.username} for {self.parent_id}"
