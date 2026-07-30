from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.core.models import USER_PATH_SYSTEM_PREFIX, Application, User, UserTypes
from authentik.lib.generators import generate_id
from authentik.lib.models import ExpiringModel

USER_PATH_AGENTS = f"{USER_PATH_SYSTEM_PREFIX}/agents"


class Agent(ExpiringModel, User):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agents")
    primary_app = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, default=None)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")

    @classmethod
    def create_for_user(
        cls, user: User, name: str = "", expiring: bool = False, expires=None
    ) -> Agent:
        # An agent is a machine identity, not a login user: mark it as a service account
        # and disable password auth. It authenticates through its issued API token.
        agent = cls.objects.create(
            username=f"agent-{generate_id()}",
            name=name,
            owner=user,
            type=UserTypes.SERVICE_ACCOUNT,
            path=USER_PATH_AGENTS,
            expiring=expiring,
            expires=expires,
        )
        agent.set_unusable_password()
        agent.save()
        return agent

    @property
    def serializer(self):
        from authentik.enterprise.agents.api import AgentSerializer

        return AgentSerializer

    def __str__(self):
        return f"Agent {self.username} for {self.owner_id}"
