"""Sync status shared by providers and directory sources"""

from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from django_dramatiq_postgres.models import TaskState
from rest_framework.fields import DateTimeField
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.kerberos.tasks import kerberos_sync
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.tasks import ldap_sync
from authentik.tasks.models import Task, TaskStatus
from authentik.tasks.schedules.common import ScheduleSpec


class SyncStatusTests(APITestCase):
    """The status action reports one actor's schedule, not every schedule on the object."""

    def setUp(self) -> None:
        self.source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldaps://ldap.example.com",
            base_dn="dc=example,dc=com",
        )
        self.client.force_login(create_test_admin_user())

    def test_ignores_schedule_for_a_different_actor(self) -> None:
        """A schedule for another actor does not count as this sync."""
        other = ScheduleSpec(
            actor=kerberos_sync,
            crontab="0 * * * *",
            identifier=generate_id(),
            rel_obj=self.source,
        ).update_or_create()
        Task.objects.create(
            actor_name=other.actor_name, state=TaskState.DONE, mtime=now(), rel_obj=other
        )

        response = self.client.get(
            reverse("authentik_api:ldapsource-sync-status", kwargs={"slug": self.source.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"is_running": False})

    def test_reports_latest_finished_task_and_latest_success(self) -> None:
        """The newest finished task and the newest successful task are separate."""
        current = now()
        other = ScheduleSpec(
            actor=kerberos_sync,
            crontab="0 * * * *",
            identifier=generate_id(),
            rel_obj=self.source,
        ).update_or_create()
        matching = ScheduleSpec(
            actor=ldap_sync,
            crontab="0 * * * *",
            identifier=generate_id(),
            rel_obj=self.source,
        ).update_or_create()
        Task.objects.create(
            actor_name=other.actor_name, state=TaskState.DONE, mtime=current, rel_obj=other
        )
        successful = Task.objects.create(
            actor_name=matching.actor_name,
            state=TaskState.DONE,
            mtime=current - timedelta(hours=2),
            rel_obj=matching,
        )
        Task.objects.create(
            actor_name=matching.actor_name,
            state=TaskState.REJECTED,
            mtime=current - timedelta(hours=1),
            rel_obj=matching,
        )
        Task.objects.create(
            actor_name=matching.actor_name,
            state=TaskState.QUEUED,
            mtime=current,
            rel_obj=matching,
        )

        response = self.client.get(
            reverse("authentik_api:ldapsource-sync-status", kwargs={"slug": self.source.slug})
        )

        successful.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "is_running": False,
                "last_sync_status": TaskStatus.REJECTED,
                "last_successful_sync": DateTimeField().to_representation(successful.mtime),
            },
        )
