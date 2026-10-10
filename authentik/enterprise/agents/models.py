from typing import Self

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from authentik.core.models import (
    USER_PATH_SYSTEM_PREFIX,
    USERNAME_MAX_LENGTH,
    Actor,
    ActorPolicyInheritance,
    User,
    UserTypes,
)
from authentik.lib.generators import generate_id

USER_PATH_AGENTS = f"{USER_PATH_SYSTEM_PREFIX}/agents"


class AgentUserQuerySet(QuerySet):
    """Select users by their agent relationship."""

    def filter_agents(self) -> Self:
        """Include only agent users."""
        return self.filter(actor__agent__isnull=False)

    def exclude_agents(self) -> Self:
        """Exclude agent users."""
        return self.filter(actor__agent__isnull=True)


class Agent(Actor):

    class Meta(Actor.Meta):
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")
        # expires/expiring live on the parent Actor table under multi-table inheritance, so the
        # indexes inherited from Actor.Meta (via ExpiringModel.Meta) don't apply to Agent itself.
        indexes = []
        permissions = [
            ("add_agent_self_service", _("Add an agent user (self-service)")),
        ]

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
            username=f"{user.username}-agent-{generate_id()}"[:USERNAME_MAX_LENGTH],
            name=name,
            parent=user,
            policy_behavior=policy_behavior,
            type=UserTypes.SERVICE_ACCOUNT,
            path=USER_PATH_AGENTS,
            expiring=expiring,
            expires=expires,
        )
        if policy_behavior == ActorPolicyInheritance.COPY:
            agent.copy_parent_policy_bindings()
        return agent

    @property
    def serializer(self):
        from authentik.enterprise.agents.api import AgentSerializer

        return AgentSerializer

    def __str__(self):
        return f"Agent {self.username} for {self.parent_id}"
