"""Membership reconciliation after signal-driven user provisioning."""

from unittest.mock import patch

from django.db import DatabaseError, transaction
from django.test import TestCase
from dramatiq.results import ResultFailure
from requests_mock import Mocker

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.lib.utils.reflection import class_to_path
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, ServiceProviderConfiguration
from authentik.providers.scim.clients.users import SCIMUserClient
from authentik.providers.scim.models import (
    SCIMMapping,
    SCIMProvider,
    SCIMProviderGroup,
    SCIMProviderUser,
)
from authentik.providers.scim.tasks import (
    scim_sync_direct,
    scim_sync_direct_dispatch,
    scim_sync_m2m,
    scim_sync_m2m_dispatch,
)


class SCIMUserMembershipTests(TestCase):
    """Execute real queued tasks in a chosen order, mocking only SCIM HTTP."""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self):
        SystemSettings.objects.update(avatars="none")
        self.http = Mocker()
        self.http.start()
        self.addCleanup(self.http.stop)
        self.config = ServiceProviderConfiguration.default()
        self.config.patch.supported = True
        self.http.get("https://localhost/ServiceProviderConfig", json=self.config.model_dump())
        self.user_id = generate_id()
        self.http.post(
            "https://localhost/Users",
            json=lambda request, _context: request.json() | {"id": self.user_id},
        )

        with sync_outgoing_inhibit_dispatch():
            self.group = Group.objects.create(name=generate_id())
        self.provider = SCIMProvider.objects.create(
            name=generate_id(), url="https://localhost", token=generate_id()
        )
        self.provider.property_mappings.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")]
        )
        self.provider.property_mappings_group.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")]
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        # Attach after configuring mappings, without starting a full sync.
        SCIMProvider.objects.filter(pk=self.provider.pk).update(backchannel_application=app)
        self.provider.refresh_from_db()
        self.remote_group = {
            "schemas": [SCIM_GROUP_SCHEMA],
            "id": generate_id(),
            "externalId": str(self.group.pk),
            "displayName": self.group.name,
            "members": [],
        }
        SCIMProviderGroup.objects.create(
            provider=self.provider,
            group=self.group,
            scim_id=self.remote_group["id"],
            attributes=self.remote_group,
        )
        self.group_url = f"https://localhost/Groups/{self.remote_group['id']}"
        self.http.get(self.group_url, json=lambda *_: self.remote_group)
        self.http.patch(self.group_url, json=self._patch_group)
        self.http.put(self.group_url, json=self._put_group)

        # The normal test broker executes tasks inline and conceals the race.
        # Keep its persistence, middleware and worker, but defer SCIM execution.
        self.pending = []
        self.process_message = scim_sync_direct.broker.worker.process_message

        def defer_scim(message):
            if message.actor_name.startswith("authentik.providers.scim.tasks."):
                self.pending.append(message)
            else:
                self.process_message(message)

        deferred = patch.object(
            scim_sync_direct.broker.worker, "process_message", side_effect=defer_scim
        )
        deferred.start()
        self.addCleanup(deferred.stop)

    def _patch_group(self, request, _context):
        for operation in request.json()["Operations"]:
            if operation["op"] == "add" and operation["path"] == "members":
                members = {member["value"] for member in self.remote_group["members"]}
                members.update(member["value"] for member in operation["value"])
                self.remote_group["members"] = [{"value": value} for value in sorted(members)]
            else:
                self.fail(f"Unexpected group operation: {operation}")
        return self.remote_group

    def _put_group(self, request, _context):
        self.remote_group.update(request.json())
        return self.remote_group

    def _run(self, actor, model=None):
        candidates = [
            message
            for message in self.pending
            if message.actor_name == actor.actor_name
            and (model is None or message.args[0] == class_to_path(model))
        ]
        self.assertEqual(len(candidates), 1, self.pending)
        message = candidates[0]
        self.pending.remove(message)
        self.process_message(message)
        # Do not let worker-caught exceptions masquerade as successful execution.
        message.get_result()

    def _create_user_with_group(self):
        # Match User Write: save the user and add membership in one transaction.
        with transaction.atomic():
            self.user = User.objects.create(username=generate_id())
            self.user.groups.add(self.group)
        self._run(scim_sync_direct_dispatch)
        self._run(scim_sync_m2m_dispatch)

    def _assert_reconciled(self):
        self.assertTrue(all(message.args[-1] == self.provider.pk for message in self.pending))
        self._run(scim_sync_direct, Group)
        self.assertEqual(self.remote_group["members"], [{"value": self.user_id}])
        self.assertEqual(self.pending, [])

    def _membership_before_user(self):
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.remote_group["members"], [])
        self._run(scim_sync_direct, User)
        self._assert_reconciled()

    def test_membership_before_user(self):
        """An early membership task must be repaired after provisioning the user."""
        self._membership_before_user()

    def test_membership_before_user_without_patch(self):
        """The follow-up must also reconcile servers that require PUT."""
        self.config.patch.supported = False
        self.http.get("https://localhost/ServiceProviderConfig", json=self.config.model_dump())
        self._membership_before_user()
        self.assertTrue(any(request.method == "PUT" for request in self.http.request_history))
        self.assertFalse(any(request.method == "PATCH" for request in self.http.request_history))

    def test_user_before_membership(self):
        """The follow-up is harmless when the original membership task succeeds."""
        self._create_user_with_group()
        self._run(scim_sync_direct, User)
        self._run(scim_sync_m2m)
        self._assert_reconciled()
        self.assertEqual(sum(request.method == "PATCH" for request in self.http.request_history), 1)

    def test_removed_before_followup(self):
        """A delayed group job reads current membership instead of replaying an add."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        with sync_outgoing_inhibit_dispatch():
            self.user.groups.remove(self.group)
        self._run(scim_sync_direct, Group)
        self.assertEqual(self.remote_group["members"], [])
        self.assertEqual(self.pending, [])

    def test_filtered_group(self):
        """Follow-ups honor group scope even when the user can be provisioned."""
        with sync_outgoing_inhibit_dispatch():
            other_group = Group.objects.create(name=generate_id())
        self.provider.group_filters.add(other_group)
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.assertTrue(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.remote_group["members"], [])
        self.assertEqual(self.pending, [])

    def test_retry_after_followup_enqueue_failure(self):
        """A retry repairs membership even though the user write is now a no-op."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        with patch.object(
            scim_sync_direct, "send_with_options", side_effect=RuntimeError("Queue unavailable")
        ):
            with self.assertRaises(ResultFailure):
                self._run(scim_sync_direct, User)
        self.assertTrue(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])

        # The test broker disables automatic retries; explicitly redeliver the task.
        scim_sync_direct.send(class_to_path(User), self.user.pk, self.provider.pk)
        self._run(scim_sync_direct, User)
        self._assert_reconciled()
        self.assertEqual(sum(request.method == "POST" for request in self.http.request_history), 1)
        self.assertFalse(any(request.method == "PUT" for request in self.http.request_history))

    def test_followup_transient_failure(self):
        """A failed group update can be retried independently of user provisioning."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.http.patch(self.group_url, status_code=503)
        with self.assertRaises(ResultFailure):
            self._run(scim_sync_direct, Group)
        self.assertEqual(self.remote_group["members"], [])

        self.http.patch(self.group_url, json=self._patch_group)
        scim_sync_direct.send(class_to_path(Group), self.group.pk, self.provider.pk)
        self._assert_reconciled()

    def test_failed_user_provisioning(self):
        """A transient user failure must not enqueue membership reconciliation."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self.http.post("https://localhost/Users", status_code=503)
        with self.assertRaises(ResultFailure):
            self._run(scim_sync_direct, User)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])

    def test_skipped_user_provisioning(self):
        """Property mappings can intentionally skip users."""
        self.provider.property_mappings.update(expression="raise SkipObject")
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])

    def test_failed_user_mapping_persistence(self):
        """The write helper may return no connection without raising an exception."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        with patch.object(SCIMUserClient, "create", side_effect=DatabaseError("Write failed")):
            self._run(scim_sync_direct, User)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])

    def test_dry_run_user_provisioning(self):
        """Rejected dry-run user creation must not enqueue group writes."""
        SCIMProvider.objects.filter(pk=self.provider.pk).update(dry_run=True)
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])
        self.assertFalse(
            any(request.method in {"POST", "PUT", "PATCH"} for request in self.http.request_history)
        )

    def test_followup_creates_missing_group(self):
        """The normal group-write path can also recover an unprovisioned group."""
        SCIMProviderGroup.objects.filter(provider=self.provider, group=self.group).delete()
        self.http.post("https://localhost/Groups", json=lambda *_: self.remote_group)
        self._membership_before_user()
        self.assertTrue(
            SCIMProviderGroup.objects.filter(provider=self.provider, group=self.group).exists()
        )
