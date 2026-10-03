"""Agent filters for user querysets."""

from typing import Self

from django.db.models import QuerySet


class AgentUserQuerySet(QuerySet):
    """Select users by their agent relationship."""

    def filter_agents(self) -> Self:
        """Include only agent users."""
        return self.filter(actor__agent__isnull=False)

    def exclude_agents(self) -> Self:
        """Exclude agent users."""
        return self.filter(actor__agent__isnull=True)
