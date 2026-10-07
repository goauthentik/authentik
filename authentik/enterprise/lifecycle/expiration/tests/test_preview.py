"""Read-only previews of saved rules and unsaved expiration-rule edits."""

from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.enterprise.lifecycle.expiration.tests.test_expiration import (
    APPLY_RULE,
    SEND_NOTIFICATION,
    ExpirationTestCase,
    _dormant_user,
)
from authentik.enterprise.lifecycle.offboarding.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.enterprise.tests import enterprise_test
from authentik.events.models import Event, Notification
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding


@enterprise_test()
class TestPreview(ExpirationTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(create_test_admin_user())
        self.group = Group.objects.create(name=generate_id())
        self.rule = self._rule(group=self.group)
        self.url = reverse("authentik_api:userexpirationrule-preview", kwargs={"pk": self.rule.pk})

    def _user(self):
        user = _dormant_user()
        user.groups.add(self.group)
        return user

    def _row(self, user):
        return UserOffboarding.objects.create(
            user=user,
            rule=self.rule,
            scheduled_at=self.rule.due_at(user),
            action=self.rule.action,
            revoke_sessions=self.rule.revoke_sessions,
            revoke_tokens=self.rule.revoke_tokens,
        )

    def test_post_has_no_side_effects(self):
        user = self._user()
        self._row(user)
        self._user()
        rules = list(UserExpirationRule.objects.order_by("pk").values())
        rows = list(UserOffboarding.objects.order_by("pk").values())
        users = list(User.objects.order_by("pk").values())
        event_count = Event.objects.count()
        notification_count = Notification.objects.count()

        with (
            patch.object(UserExpirationRule, "_warn") as warn,
            patch(SEND_NOTIFICATION) as notify,
            patch(APPLY_RULE) as dispatch,
        ):
            response = self.client.post(
                self.url,
                {
                    "name": generate_id(),
                    "action": OffboardingAction.DELETE,
                    "inactivity_duration": "days=30",
                    "revoke_sessions": False,
                },
                format="json",
            )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["updated"]["count"], 1)
        warn.assert_not_called()
        notify.assert_not_called()
        dispatch.assert_not_called()
        self.assertEqual(list(UserExpirationRule.objects.order_by("pk").values()), rules)
        self.assertEqual(list(UserOffboarding.objects.order_by("pk").values()), rows)
        self.assertEqual(list(User.objects.order_by("pk").values()), users)
        self.assertEqual(Event.objects.count(), event_count)
        self.assertEqual(Notification.objects.count(), notification_count)

    def test_post_delete_shows_pending_action_and_revocation_changes(self):
        user = self._user()
        row = self._row(user)
        response = self.client.post(
            self.url,
            {"action": OffboardingAction.DELETE, "revoke_sessions": False, "revoke_tokens": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["updated"]["count"], 1)
        updated = response.data["updated"]["offboardings"][0]
        self.assertEqual(updated["id"], str(row.pk))
        self.assertEqual(updated["user"]["pk"], user.pk)
        self.assertEqual(updated["previous_action"], OffboardingAction.DEACTIVATE)
        self.assertEqual(updated["action"], OffboardingAction.DELETE)
        self.assertEqual(parse_datetime(updated["previous_scheduled_at"]), row.scheduled_at)
        self.assertEqual(parse_datetime(updated["scheduled_at"]), row.scheduled_at)
        self.assertTrue(updated["previous_revoke_sessions"])
        self.assertFalse(updated["revoke_sessions"])
        self.assertTrue(updated["previous_revoke_tokens"])
        self.assertFalse(updated["revoke_tokens"])
        row.refresh_from_db()
        self.assertEqual(row.action, OffboardingAction.DEACTIVATE)

    def test_narrowing_scope_previews_removals_and_remaining_new_candidates(self):
        narrower = Group.objects.create(name=generate_id())
        outside = self._user()
        removed_row = self._row(outside)
        kept = self._user()
        kept.groups.add(narrower)
        kept_row = self._row(kept)
        new = self._user()
        new.groups.add(narrower)

        response = self.client.post(self.url, {"group": str(narrower.pk)}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["users"][0]["pk"], new.pk)
        self.assertEqual(response.data["updated"]["count"], 0)
        self.assertEqual(response.data["removed"]["count"], 1)
        removed = response.data["removed"]["offboardings"][0]
        self.assertEqual(removed["id"], str(removed_row.pk))
        self.assertEqual(removed["user"]["pk"], outside.pk)
        for field in ("action", "scheduled_at", "revoke_sessions", "revoke_tokens"):
            self.assertIsNone(removed[field])
        self.assertTrue(UserOffboarding.objects.filter(pk=removed_row.pk).exists())
        self.assertTrue(UserOffboarding.objects.filter(pk=kept_row.pk).exists())
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.group, self.group)

    @freeze_time()
    def test_withdrawn_rows_are_excluded_before_counting_new_candidates(self):
        # A missed withdrawal can remove and then recreate a row in the same sweep
        # when activity still falls inside the edited rule's warning window. Use
        # more rows than the sample limit to cover withdrawals outside the sample.
        rows = []
        for _ in range(21):
            user = self._user()
            rows.append(self._row(user))
            User.objects.filter(pk=user.pk).update(last_login=now() - timedelta(days=1))
        UserOffboarding.objects.filter(pk__in=[row.pk for row in rows]).update(
            created_at=now() - timedelta(days=2)
        )
        response = self.client.post(
            self.url, {"inactivity_duration": "days=2", "warn_before": "days=1"}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["removed"]["count"], 21)
        self.assertEqual(len(response.data["removed"]["offboardings"]), 20)
        self.assertEqual(response.data["count"], 21)
        self.assertEqual(len(response.data["users"]), 20)
        self.assertEqual(
            UserOffboarding.objects.filter(pk__in=[row.pk for row in rows]).count(), 21
        )

    def test_earlier_rule_previews_takeover_with_before_and_after_settings(self):
        user = self._user()
        owner = self._rule(
            group=self.group,
            inactivity_duration="days=120",
            warn_before="days=30",
            action=OffboardingAction.DELETE,
            revoke_sessions=False,
            revoke_tokens=False,
        )
        row = UserOffboarding.objects.create(
            user=user,
            rule=owner,
            scheduled_at=owner.due_at(user),
            action=owner.action,
            revoke_sessions=False,
            revoke_tokens=False,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["taken_over"]["count"], 1)
        takeover = response.data["taken_over"]["offboardings"][0]
        self.assertEqual(takeover["id"], str(row.pk))
        self.assertEqual(takeover["previous_action"], OffboardingAction.DELETE)
        self.assertEqual(takeover["action"], OffboardingAction.DEACTIVATE)
        self.assertEqual(parse_datetime(takeover["previous_scheduled_at"]), row.scheduled_at)
        self.assertEqual(parse_datetime(takeover["scheduled_at"]), self.rule.due_at(user))
        self.assertFalse(takeover["previous_revoke_sessions"])
        self.assertTrue(takeover["revoke_sessions"])
        self.assertFalse(takeover["previous_revoke_tokens"])
        self.assertTrue(takeover["revoke_tokens"])
        row.refresh_from_db()
        self.assertEqual(row.rule, owner)

    def test_takeover_ties_use_the_least_destructive_action(self):
        for owner_action, proposed_action, expected in (
            (OffboardingAction.DELETE, OffboardingAction.DEACTIVATE, 1),
            (OffboardingAction.DEACTIVATE, OffboardingAction.DELETE, 0),
        ):
            with self.subTest(owner_action=owner_action, proposed_action=proposed_action):
                group = Group.objects.create(name=generate_id())
                rule = self._rule(group=group)
                owner = self._rule(group=group, action=owner_action)
                user = _dormant_user()
                user.groups.add(group)
                row = UserOffboarding.objects.create(
                    user=user, rule=owner, scheduled_at=owner.due_at(user), action=owner.action
                )
                response = self.client.post(
                    reverse("authentik_api:userexpirationrule-preview", kwargs={"pk": rule.pk}),
                    {"action": proposed_action},
                    format="json",
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["taken_over"]["count"], expected)
                row.refresh_from_db()
                self.assertEqual(row.rule, owner)

    def test_disabled_rule_is_previewed_as_enabled_without_enabling_it(self):
        user = self._user()
        row = self._row(user)
        UserOffboarding.objects.filter(pk=row.pk).update(
            scheduled_at=row.scheduled_at + timedelta(days=1)
        )
        self._user()
        UserExpirationRule.objects.filter(pk=self.rule.pk).update(enabled=False)
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = (
                    self.client.get(self.url)
                    if method == "get"
                    else self.client.post(self.url, {"enabled": False}, format="json")
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["count"], 1)
                self.assertEqual(response.data["updated"]["count"], 1)
                self.assertEqual(response.data["removed"]["count"], 0)
                self.rule.refresh_from_db()
                self.assertFalse(self.rule.enabled)

    def test_view_permission_is_sufficient_for_get_and_post(self):
        self._user()
        for object_permission in (False, True):
            with self.subTest(object_permission=object_permission):
                viewer = create_test_user()
                viewer.assign_perms_to_managed_role(
                    "authentik_lifecycle.view_userexpirationrule",
                    obj=self.rule if object_permission else None,
                )
                self.client.force_login(viewer)
                self.assertFalse(viewer.has_perm("authentik_lifecycle.add_userexpirationrule"))
                self.assertFalse(
                    viewer.has_perm("authentik_lifecycle.change_userexpirationrule", self.rule)
                )
                for method in ("get", "post"):
                    with self.subTest(method=method):
                        response = (
                            self.client.get(self.url)
                            if method == "get"
                            else self.client.post(
                                self.url, {"action": OffboardingAction.DELETE}, format="json"
                            )
                        )
                        self.assertEqual(response.status_code, 200, response.data)
                        self.assertEqual(response.data["count"], 1)

    def test_preview_requires_view_permission_on_the_selected_rule(self):
        viewer = create_test_user()
        other = self._rule()
        viewer.assign_perms_to_managed_role("authentik_lifecycle.view_userexpirationrule", other)
        self.client.force_login(viewer)
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = (
                    self.client.get(self.url)
                    if method == "get"
                    else self.client.post(
                        self.url, {"action": OffboardingAction.DELETE}, format="json"
                    )
                )
                self.assertEqual(response.status_code, 403, response.data)

    def test_manual_rows_terminal_exemptions_and_unchanged_rows_are_preserved(self):
        manual_user = self._user()
        UserOffboarding.objects.create(user=manual_user, scheduled_at=now() + timedelta(days=1))
        canceled_user = self._user()
        UserOffboarding.objects.create(
            user=canceled_user,
            rule=self.rule,
            scheduled_at=self.rule.due_at(canceled_user),
            status=OffboardingStatus.CANCELED,
            executed_at=now(),
        )
        self._row(self._user())
        new = self._user()
        rows = list(UserOffboarding.objects.order_by("pk").values())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["users"][0]["pk"], new.pk)
        for change in ("updated", "taken_over", "removed"):
            self.assertEqual(response.data[change], {"count": 0, "offboardings": []})
        self.assertEqual(list(UserOffboarding.objects.order_by("pk").values()), rows)

    def test_post_preserves_existing_policy_bindings(self):
        self._row(self._user())
        self._user()
        foreign_user = self._user()
        owner = self._rule(group=self.group, inactivity_duration="days=120", warn_before="days=30")
        UserOffboarding.objects.create(
            user=foreign_user, rule=owner, scheduled_at=owner.due_at(foreign_user)
        )
        PolicyBinding.objects.create(
            target=self.rule,
            policy=DummyPolicy.objects.create(
                name=generate_id(), result=False, wait_min=0, wait_max=1
            ),
            order=0,
        )
        response = self.client.post(self.url, {"action": OffboardingAction.DELETE}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["updated"]["count"], 0)
        self.assertEqual(response.data["taken_over"]["count"], 0)
        self.assertEqual(response.data["removed"]["count"], 1)
        self.assertEqual(UserOffboarding.objects.count(), 2)

    def test_post_rejects_invalid_settings_and_missing_license(self):
        row = self._row(self._user())
        response = self.client.post(self.url, {"warn_before": "days=90"}, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("warn_before", response.data)
        with patch("authentik.enterprise.license.LicenseKey.cached_summary") as summary:
            summary.return_value.status.is_valid = False
            response = self.client.post(
                self.url, {"action": OffboardingAction.DELETE}, format="json"
            )
        self.assertEqual(response.status_code, 400, response.data)
        row.refresh_from_db()
        self.assertEqual(row.action, OffboardingAction.DEACTIVATE)
