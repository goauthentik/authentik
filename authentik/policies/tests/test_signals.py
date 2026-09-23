"""Tests for policy cache invalidation.

Policy and binding changes must invalidate cached results, while ``last_login``-
only User saves must avoid the broad ``cache.keys(...)`` invalidation.
"""

from unittest import TestCase, mock
from uuid import UUID

from authentik.core.models import User
from authentik.policies import signals
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.types import CACHE_PREFIX


class _FakeUser:
    pk = 1


class _FakePolicy:
    pk = "fake-policy-pk"


class _FakeBinding:
    policy_binding_uuid = UUID("12345678-1234-5678-1234-567812345678")


class TestInvalidatePolicyCache(TestCase):
    """Test policy and application cache invalidation."""

    def _run_handler(self, sender, instance, update_fields, policy_bindings=()):
        """Run the handler with mocked cache/PolicyBinding; return the
        cache mock for assertions."""

        with (
            mock.patch.object(signals, "cache") as mock_cache,
            mock.patch.object(signals, "PolicyBinding") as mock_pb,
        ):
            mock_cache.keys.return_value = []
            mock_pb.objects.filter.return_value = policy_bindings
            signals.invalidate_policy_cache(
                sender=sender,
                instance=instance,
                update_fields=update_fields,
            )
            return mock_cache

    def test_user_save_with_only_last_login_does_not_invalidate(self):
        """User save with update_fields=["last_login"] is the per-login hot
        path. The handler must short-circuit without touching the cache."""
        mock_cache = self._run_handler(
            sender=User, instance=_FakeUser(), update_fields=["last_login"]
        )
        mock_cache.keys.assert_not_called()
        mock_cache.delete_many.assert_not_called()

    def test_user_save_with_last_login_as_set_does_not_invalidate(self):
        """``update_fields`` may be a set (Django supports any iterable).
        The handler must treat ``{"last_login"}`` identically to
        ``["last_login"]``."""
        mock_cache = self._run_handler(
            sender=User, instance=_FakeUser(), update_fields={"last_login"}
        )
        mock_cache.keys.assert_not_called()

    def test_user_save_with_other_fields_still_invalidates(self):
        """A User save that updates ``email`` (or any non-last_login field)
        must still invalidate the cache — those updates can affect policy
        evaluation, group membership computation, etc."""
        mock_cache = self._run_handler(sender=User, instance=_FakeUser(), update_fields=["email"])
        mock_cache.keys.assert_called()
        mock_cache.delete_many.assert_called()

    def test_user_save_with_last_login_plus_other_fields_invalidates(self):
        """If ``update_fields`` contains ``last_login`` plus anything else,
        we must invalidate — the other field could have policy implications."""
        mock_cache = self._run_handler(
            sender=User,
            instance=_FakeUser(),
            update_fields=["last_login", "email"],
        )
        mock_cache.keys.assert_called()

    def test_user_save_without_update_fields_invalidates(self):
        """``update_fields=None`` means a full save — anything could have
        changed, so we conservatively invalidate."""
        mock_cache = self._run_handler(sender=User, instance=_FakeUser(), update_fields=None)
        mock_cache.keys.assert_called()

    def test_policy_save_still_invalidates(self):
        """Non-User senders are unaffected by the new short-circuit.
        Policy/PolicyBinding/PolicyBindingModel/Group saves must continue to
        invalidate as before — those changes affect access decisions for
        every user."""
        binding = _FakeBinding()
        mock_cache = self._run_handler(
            sender=Policy,
            instance=_FakePolicy(),
            update_fields=["last_login"],  # irrelevant — sender isn't User
            policy_bindings=[binding],
        )
        mock_cache.keys.assert_any_call(f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}_*")
        mock_cache.delete_many.assert_called()

    def test_policy_binding_save_invalidates_binding_cache(self):
        """Binding updates invalidate every cached result for that binding."""
        binding = _FakeBinding()
        with mock.patch.object(signals, "cache") as mock_cache:
            mock_cache.keys.side_effect = [["policy-cache-key"], []]

            signals.invalidate_policy_cache(
                sender=PolicyBinding,
                instance=binding,
            )

        mock_cache.keys.assert_any_call(f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}_*")
        mock_cache.delete_many.assert_any_call(["policy-cache-key"])


class TestInvalidateUserApplicationCacheMembership(TestCase):
    """Test application-cache invalidation for group membership changes."""

    def test_user_side_add_invalidates_all_list_variants(self):
        """Adding a group through ``user.groups`` invalidates that user only."""
        user = _FakeUser()
        with mock.patch.object(signals, "cache") as mock_cache:
            mock_cache.keys.return_value = ["cached-page", "cached-launch-page"]

            signals.invalidate_user_application_cache_membership(
                sender=object,
                instance=user,
                action="post_add",
                reverse=False,
                pk_set={2},
            )

        mock_cache.keys.assert_called_once_with(f"{signals.user_app_cache_key(user.pk)}/*")
        mock_cache.delete_many.assert_called_once_with(["cached-page", "cached-launch-page"])

    def test_group_side_remove_invalidates_affected_users(self):
        """Removing users through ``group.users`` invalidates each affected user."""
        with mock.patch.object(signals, "cache") as mock_cache:
            mock_cache.keys.side_effect = [["user-1-page"], ["user-2-page"]]

            signals.invalidate_user_application_cache_membership(
                sender=object,
                instance=object(),
                action="post_remove",
                reverse=True,
                pk_set={1, 2},
            )

        self.assertEqual(mock_cache.keys.call_count, 2)
        mock_cache.delete_many.assert_called_once_with(["user-1-page", "user-2-page"])

    def test_group_side_clear_resolves_users_before_clear(self):
        """Reverse ``clear`` resolves affected users during ``pre_clear``."""
        group = mock.Mock()
        group.users.values_list.return_value = [1, 2]
        with mock.patch.object(signals, "invalidate_user_application_cache") as invalidate:
            signals.invalidate_user_application_cache_membership(
                sender=object,
                instance=group,
                action="pre_clear",
                reverse=True,
                pk_set=None,
            )

        group.users.values_list.assert_called_once_with("pk", flat=True)
        invalidate.assert_called_once_with([1, 2])

    def test_unrelated_m2m_phase_does_not_invalidate(self):
        """Pre-add and post-clear phases do not duplicate invalidation."""
        with mock.patch.object(signals, "invalidate_user_application_cache") as invalidate:
            for action in ("pre_add", "pre_remove", "post_clear"):
                signals.invalidate_user_application_cache_membership(
                    sender=object,
                    instance=_FakeUser(),
                    action=action,
                    reverse=False,
                    pk_set={2},
                )

        invalidate.assert_not_called()
