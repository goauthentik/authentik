from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.core.models import Application, User
from authentik.lib.generators import generate_id
from authentik.lib.models import ExpiringModel


class Agent(ExpiringModel, User):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agents")
    primary_app = models.ForeignKey(
        Application, on_delete=models.CASCADE, null=True, default=None
    )

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")

    @classmethod
    def create_for_user(
        cls, user: User, name: str = "", expiring: bool = False, expires=None
    ) -> "Agent":
        return cls.objects.create(
            username=f"agent-{generate_id()}",
            name=name,
            owner=user,
            expiring=expiring,
            expires=expires,
        )

    @property
    def serializer(self):
        from authentik.enterprise.agents.api import AgentSerializer

        return AgentSerializer

    def __str__(self):
        return f"Agent {self.username} for {self.owner_id}"
