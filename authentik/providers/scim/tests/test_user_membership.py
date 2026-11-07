"""Membership reconciliation after signal-driven user provisioning."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import patch

from django.db import DatabaseError, close_old_connections, connections, transaction
from django.test import TestCase, TransactionTestCase
from dramatiq.results import ResultFailure
from requests_mock import Mocker

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.lib.utils.reflection import class_to_path
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, ServiceProviderConfiguration
from authentik.providers.scim.clients.users import SCIMUserClient
from authentik.providers.scim.models import (
    SCIMCompatibilityMode,
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
    scim_sync_user_memberships,
)
from authentik.tasks.models import Task


class SCIMUserMembershipTestMixin:
    """Execute real queued tasks in a chosen order, mocking only SCIM HTTP."""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self):
        SystemSettings.objects.update(avatars="none")
        self.http = Mocker()
        self.http.start()
        self.addCleanup(self.http.stop)
        self.config = ServiceProviderConfiguration.default()
        self.config.patch.supported = True
        self.config.filter.supported = True
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
        self._run(scim_sync_user_memberships)
        self.assertEqual(self.remote_group["members"], [{"value": self.user_id}])
        self.assertEqual(self.pending, [])

    def _membership_before_user(self):
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.remote_group["members"], [])
        self._run(scim_sync_direct, User)
        self._assert_reconciled()


class SCIMUserMembershipTests(SCIMUserMembershipTestMixin, TestCase):
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
        # A targeted, idempotent add avoids reading the entire group to deduplicate it.
        self.assertEqual(sum(request.method == "PATCH" for request in self.http.request_history), 2)
        self.assertFalse(
            any(
                request.url == self.group_url and request.method == "GET"
                for request in self.http.request_history
            )
        )

    def test_removed_before_followup(self):
        """A delayed group job reads current membership instead of replaying an add."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        with sync_outgoing_inhibit_dispatch():
            self.user.groups.remove(self.group)
        self._run(scim_sync_user_memberships)
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
        self._run(scim_sync_user_memberships)
        self.assertEqual(self.remote_group["members"], [])
        self.assertEqual(self.pending, [])

    def test_retry_after_followup_enqueue_failure(self):
        """Rollback the mapping if dispatch fails, then adopt the remote user on retry."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        with patch.object(
            scim_sync_user_memberships,
            "send_with_options",
            side_effect=RuntimeError("Queue unavailable"),
        ):
            with self.assertRaises(ResultFailure):
                self._run(scim_sync_direct, User)
        self.assertFalse(SCIMProviderUser.objects.filter(user=self.user).exists())
        self.assertEqual(self.pending, [])

        # The HTTP creation survived the local rollback. Exercise conflict adoption
        # instead of pretending a second POST creates the same user again.
        payload = next(
            request.json() for request in self.http.request_history if request.method == "POST"
        )
        self.http.post("https://localhost/Users", status_code=409)
        self.http.get(
            "https://localhost/Users", json={"Resources": [payload | {"id": self.user_id}]}
        )
        # The test broker disables automatic retries; explicitly redeliver the task.
        scim_sync_direct.send(class_to_path(User), self.user.pk, self.provider.pk)
        self._run(scim_sync_direct, User)
        self._assert_reconciled()
        self.assertEqual(sum(request.method == "POST" for request in self.http.request_history), 2)
        self.assertFalse(any(request.method == "PUT" for request in self.http.request_history))

    def test_followup_transient_failure(self):
        """A failed group update can be retried independently of user provisioning."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.http.patch(self.group_url, status_code=503)
        with self.assertRaises(ResultFailure):
            self._run(scim_sync_user_memberships)
        self.assertEqual(self.remote_group["members"], [])

        self.http.patch(self.group_url, json=self._patch_group)
        scim_sync_user_memberships.send(self.user.pk, self.provider.pk)
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

    def test_noop_user_sync_does_not_enqueue_memberships(self):
        """Repeated user updates must not fan out into group jobs or group reads."""
        self._membership_before_user()
        self.http.reset_mock()
        for _ in range(3):
            scim_sync_direct.send(class_to_path(User), self.user.pk, self.provider.pk)
            self._run(scim_sync_direct, User)
            self.assertEqual(self.pending, [])
        self.assertEqual(self.http.call_count, 0)

    def test_changed_user_does_not_enqueue_memberships(self):
        """A profile update only writes the user, not their groups."""
        self._membership_before_user()
        self.http.reset_mock()
        self.http.put(f"https://localhost/Users/{self.user_id}", json={"id": self.user_id})
        self.user.name = generate_id()
        self.user.save()
        self._run(scim_sync_direct_dispatch)
        self._run(scim_sync_direct, User)
        self.assertEqual(self.pending, [])
        self.assertEqual([request.method for request in self.http.request_history], ["PUT"])

    def _preserve_other_members(self, patch_supported):
        self.config.patch.supported = patch_supported
        self.http.get("https://localhost/ServiceProviderConfig", json=self.config.model_dump())
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        with sync_outgoing_inhibit_dispatch():
            other_user = User.objects.create(username=generate_id())
            other_user.groups.add(self.group)
        # Another local member is present remotely, but their SCIM mapping is not
        # available yet. Repairing this user must not remove that other member.
        other_id = generate_id()
        other_member = {"value": other_id, "display": other_user.username}
        self.remote_group["members"] = [other_member]
        self._run(scim_sync_direct, User)
        self.http.reset_mock()
        self._run(scim_sync_user_memberships)
        self.assertFalse(SCIMProviderUser.objects.filter(user=other_user).exists())
        self.assertEqual(
            {member["value"] for member in self.remote_group["members"]},
            {other_id, self.user_id},
        )
        if patch_supported:
            self.assertEqual([request.method for request in self.http.request_history], ["PATCH"])
            operations = self.http.last_request.json()["Operations"]
            self.assertEqual(
                operations, [{"op": "add", "path": "members", "value": [{"value": self.user_id}]}]
            )
        else:
            self.assertEqual(
                [request.method for request in self.http.request_history], ["GET", "PUT"]
            )
            self.assertIn(other_member, self.remote_group["members"])

    def test_patch_followup_preserves_unmapped_member(self):
        self._preserve_other_members(patch_supported=True)

    def test_put_followup_preserves_unmapped_member(self):
        self._preserve_other_members(patch_supported=False)

    def test_aws_followup_only_adds_new_user(self):
        """AWS group reads cannot enumerate members; add only the provisioned user."""
        SCIMProvider.objects.filter(pk=self.provider.pk).update(
            compatibility_mode=SCIMCompatibilityMode.AWS
        )
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.http.reset_mock()
        # A target that cannot read its member list still supports targeted PATCH.
        self.http.get(self.group_url, status_code=405)
        self._assert_reconciled()
        self.assertEqual([request.method for request in self.http.request_history], ["PATCH"])

    def test_followup_without_service_provider_config(self):
        """Retain the targeted PATCH fallback for providers without discovery/PUT."""
        self.http.get("https://localhost/ServiceProviderConfig", status_code=404)
        self.http.get(self.group_url, status_code=405)
        self._membership_before_user()

    def test_membership_rechecked_after_group_lock(self):
        """A removal while waiting for the lock must not be overwritten by the repair."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.http.reset_mock()
        object_lock = SCIMGroupClient.object_lock

        @contextmanager
        def remove_while_waiting(client, group):
            with object_lock(client, group):
                with sync_outgoing_inhibit_dispatch():
                    self.user.groups.remove(group)
                yield

        with patch.object(
            SCIMGroupClient, "object_lock", autospec=True, side_effect=remove_while_waiting
        ):
            self._run(scim_sync_user_memberships)
        self.assertEqual(self.http.call_count, 0)
        self.assertEqual(self.remote_group["members"], [])

    def test_redelivered_user_does_not_duplicate_pending_followup(self):
        """A crash after commit leaves the durable follow-up, not another fan-out."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        self._run(scim_sync_direct, User)
        self.assertEqual(len(self.pending), 1)
        followup_id = self.pending[0].message_id
        scim_sync_direct.send(class_to_path(User), self.user.pk, self.provider.pk)
        self._run(scim_sync_direct, User)
        self.assertEqual([message.message_id for message in self.pending], [followup_id])
        self._assert_reconciled()


class SCIMUserMembershipTransactionTests(SCIMUserMembershipTestMixin, TransactionTestCase):
    def test_mapping_and_followup_commit_together(self):
        """A different worker can only see the mapping and its job after commit."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)

        def visible_from_worker():
            close_old_connections()
            try:
                return (
                    SCIMProviderUser.objects.filter(
                        user=self.user, provider=self.provider
                    ).exists(),
                    Task.objects.filter(actor_name=scim_sync_user_memberships.actor_name).exists(),
                )
            finally:
                connections.close_all()

        send = scim_sync_user_memberships.send_with_options
        with ThreadPoolExecutor(max_workers=1) as executor:

            def enqueue_before_commit(**kwargs):
                message = send(**kwargs)
                self.assertEqual(
                    executor.submit(visible_from_worker).result(timeout=5), (False, False)
                )
                return message

            with patch.object(
                scim_sync_user_memberships, "send_with_options", side_effect=enqueue_before_commit
            ):
                self._run(scim_sync_direct, User)
            self.assertEqual(executor.submit(visible_from_worker).result(timeout=5), (True, True))
        self._assert_reconciled()

    def test_dispatch_failure_rolls_back_mapping_and_job(self):
        """Even an exception after enqueueing cannot leave an orphan mapping or job."""
        self._create_user_with_group()
        self._run(scim_sync_m2m)
        send = scim_sync_user_memberships.send_with_options

        def enqueue_then_fail(**kwargs):
            send(**kwargs)
            raise RuntimeError("Dispatch interrupted")

        with patch.object(
            scim_sync_user_memberships, "send_with_options", side_effect=enqueue_then_fail
        ):
            with self.assertRaises(ResultFailure):
                self._run(scim_sync_direct, User)
        self.assertFalse(
            SCIMProviderUser.objects.filter(user=self.user, provider=self.provider).exists()
        )
        self.assertFalse(
            Task.objects.filter(actor_name=scim_sync_user_memberships.actor_name).exists()
        )
