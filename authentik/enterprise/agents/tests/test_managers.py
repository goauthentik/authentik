"""Agent filters on the user manager and querysets."""

from django.test import TestCase

from authentik.core.models import Actor, ActorPolicyInheritance, User, UserTypes
from authentik.enterprise.agents.models import Agent


class AgentUserQuerySetTests(TestCase):
    """Agent filters preserve other user types and ordinary actors."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username="owner")
        cls.service = User.objects.create(username="service", type=UserTypes.SERVICE_ACCOUNT)
        cls.actor = Actor.for_user(cls.owner, ActorPolicyInheritance.NONE)
        cls.users = [
            cls.owner,
            User.objects.create(username="external", type=UserTypes.EXTERNAL),
            cls.service,
            User.objects.create(
                username="internal-service", type=UserTypes.INTERNAL_SERVICE_ACCOUNT
            ),
            cls.actor,
        ]
        cls.agent = Agent.create_for_user(cls.owner)

    def test_agent_filters(self):
        """Manager and chained filters distinguish agents from ordinary service accounts."""
        non_agent_pks = {user.pk for user in self.users}
        pks = non_agent_pks | {self.agent.pk}
        for users in (User.objects, User.objects.filter(pk__in=pks)):
            with self.subTest(entrypoint=type(users)):
                with self.assertNumQueries(1):
                    self.assertSetEqual(
                        set(users.filter_agents().filter(pk__in=pks).values_list("pk", flat=True)),
                        {self.agent.pk},
                    )
                with self.assertNumQueries(1):
                    self.assertSetEqual(
                        set(users.exclude_agents().filter(pk__in=pks).values_list("pk", flat=True)),
                        non_agent_pks,
                    )

    def test_chained_filters_preserve_scope(self):
        """Agent filters compose with user type filters and anonymous-user exclusion."""
        services = User.objects.exclude_anonymous().filter(type=UserTypes.SERVICE_ACCOUNT)
        self.assertQuerySetEqual(
            services.filter_agents(), [self.agent.pk], transform=lambda u: u.pk
        )
        self.assertQuerySetEqual(
            services.exclude_agents(),
            [self.service.pk, self.actor.pk],
            transform=lambda u: u.pk,
            ordered=False,
        )
        self.assertFalse(User.objects.filter(pk=self.owner.pk).filter_agents().exists())
        self.assertFalse(User.objects.filter_agents().exclude_agents().exists())
