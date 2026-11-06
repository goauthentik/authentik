"""Preserve existing application grants when making the through model explicit."""

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase

from authentik.core.models import Application
from authentik.enterprise.agents.models import Agent
from authentik.lib.generators import generate_id


class TestAgentApplicationMigration(TestCase):
    def test_existing_links_survive_forward_and_reverse(self):
        agent = Agent.create_for_user(None)
        application = Application.objects.create(name=generate_id(), slug=generate_id())
        loader = MigrationLoader(connection)
        before = loader.project_state(
            ("authentik_agents", "0002_agent_applications_agent_id_jag_audience_and_more")
        )
        old_agent = before.apps.get_model("authentik_agents", "Agent")
        old_through = old_agent._meta.get_field("applications").remote_field.through
        link = old_through.objects.create(agent_id=agent.pk, application_id=application.pk)
        migration = loader.get_migration("authentik_agents", "0003_agent_application")

        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                after = migration.apply(before.clone(), editor)
        new_through = after.apps.get_model("authentik_agents", "AgentApplication")
        self.assertEqual(
            new_through.objects.values_list("agent_id", "application_id").get(pk=link.pk),
            (agent.pk, application.pk),
        )
        self.assertEqual(list(agent.applications.all()), [application])

        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                migration.unapply(before.clone(), editor)
        self.assertEqual(
            old_through.objects.values_list("agent_id", "application_id").get(pk=link.pk),
            (agent.pk, application.pk),
        )
