"""Sync status shared by providers and directory sources"""

import json
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils.timezone import now
from django_dramatiq_postgres.models import TaskState
from dramatiq.actor import Actor
from rest_framework.fields import DateTimeField
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from authentik.lib.generators import generate_id
from authentik.sources.kerberos.tasks import kerberos_sync
from authentik.sources.ldap.api.sources import LDAPSourceViewSet
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.tasks import ldap_sync
from authentik.tasks.models import Task, TaskStatus
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import Schedule


class SyncStatusTests(TestCase):
    """The status action reports one actor's schedule, not every schedule on the object."""

    def _source(self) -> LDAPSource:
        return LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldaps://ldap.example.com",
            base_dn="dc=example,dc=com",
        )

    def _schedule(self, source: LDAPSource, actor: Actor) -> Schedule:
        return ScheduleSpec(
            actor=actor,
            crontab="0 * * * *",
            identifier=generate_id(),
            rel_obj=source,
        ).update_or_create()

    def _status(self, source: LDAPSource) -> Response:
        view = LDAPSourceViewSet()
        view.get_object = lambda: source
        return view.sync_status(APIRequestFactory().get("/"))

    def _task(self, schedule: Schedule, state: str, mtime: datetime) -> Task:
        return Task.objects.create(
            actor_name=schedule.actor_name,
            state=state,
            mtime=mtime,
            rel_obj=schedule,
        )

    def test_ignores_schedule_for_a_different_actor(self) -> None:
        """A schedule for another actor does not count as this sync."""
        source = self._source()
        schedule = self._schedule(source, kerberos_sync)
        self._task(schedule, TaskState.DONE, now())

        response = self._status(source)

        self.assertJSONEqual(json.dumps(response.data), {"is_running": False})

    def test_reports_latest_finished_task_and_latest_success(self) -> None:
        """The newest finished task and the newest successful task are separate."""
        source = self._source()
        current = now()
        other = self._schedule(source, kerberos_sync)
        matching = self._schedule(source, ldap_sync)
        self._task(other, TaskState.DONE, current)
        successful = self._task(matching, TaskState.DONE, current - timedelta(hours=2))
        self._task(matching, TaskState.REJECTED, current - timedelta(hours=1))
        self._task(matching, TaskState.QUEUED, current)

        response = self._status(source)

        successful.refresh_from_db()
        self.assertJSONEqual(
            json.dumps(response.data),
            {
                "is_running": False,
                "last_sync_status": TaskStatus.REJECTED,
                "last_successful_sync": DateTimeField().to_representation(successful.mtime),
            },
        )
