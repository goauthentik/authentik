"""Tests for policy cache invalidation.

Policy and binding changes must invalidate cached results, while ``last_login``-
only User saves and user creation must avoid the broad ``cache.keys(...)``
invalidation, and other User saves must only invalidate that user's entries.
"""

from fnmatch import fnmatchcase
from unittest import TestCase, mock
from uuid import UUID

from authentik.core.api.applications import user_app_cache_key
from authentik.core.models import Group, User
from authentik.policies import signals
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.types import CACHE_PREFIX


class _FakeUser:
    def __init__(self, pk=1):
        self.pk = pk


class _FakePolicy:
    pk = "fake-policy-pk"


class _FakeBinding:
    policy_binding_uuid = UUID("12345678-1234-5678-1234-567812345678")


class _FakeCache:
    """Minimal cache stand-in: stores keys, matches glob patterns, records
    deletions. Mirrors the postgres-backed cache closely enough to assert
    which rows a save would lock."""

    def __init__(self, stored):
        self._stored = set(stored)
        self.deleted = []

    def keys(self, pattern):
        return sorted(key for key in self._stored if fnmatchcase(key, pattern))

    def delete_many(self, keys):
        for key in keys:
            self.deleted.append(key)
            self._stored.discard(key)


def _app_access_keys(*pks):
    """The full set of application-list cache entries for the given users,
    covering every suffix ``user_app_cache_key`` can produce."""
    keys = set()
    for pk in pks:
        keys.add(user_app_cache_key(str(pk)))
        keys.add(user_app_cache_key(str(pk), only_with_launch_url=True))
        keys.add(user_app_cache_key(str(pk), client_ip="10.0.0.1"))
        keys.add(user_app_cache_key(str(pk), page_number=2))
        keys.add(user_app_cache_key(str(pk), client_ip="10.0.0.1", page_number=2))
        keys.add(
            user_app_cache_key(
                str(pk), client_ip="10.0.0.1", page_number=2, only_with_launch_url=True
            )
        )
    return keys


class TestInvalidatePolicyCache(TestCase):
    """Test policy and application cache invalidation."""

    def _run_handler(self, sender, instance, update_fields, policy_bindings=(), created=False):
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
                created=created,
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

    def test_user_create_does_not_invalidate(self):
        """A freshly created user has no cached entries, and creating a user
        cannot change any other user's access — the cache must not be touched
        at all. This is the enrollment hot path: concurrent creations used to
        issue overlapping cache-table DELETEs that deadlocked Postgres."""
        mock_cache = self._run_handler(
            sender=User, instance=_FakeUser(), update_fields=None, created=True
        )
        mock_cache.keys.assert_not_called()
        mock_cache.delete_many.assert_not_called()

    def test_user_save_scopes_invalidation_to_saved_user(self):
        """A User save must only delete that user's own application-list
        entries — every variant of the user's key, and nothing belonging to
        any other user. The pattern must not leak across pk prefixes
        (user 7 must not match user 70)."""
        stored = _app_access_keys(7, 70)
        fake_cache = _FakeCache(stored)
        with mock.patch.object(signals, "cache", fake_cache):
            signals.invalidate_policy_cache(
                sender=User, instance=_FakeUser(pk=7), update_fields=["email"]
            )
        self.assertCountEqual(fake_cache.deleted, _app_access_keys(7))
        self.assertEqual(fake_cache._stored, _app_access_keys(70))

    def test_user_save_with_last_login_plus_other_fields_invalidates(self):
        """If ``update_fields`` contains ``last_login`` plus anything else,
        we must invalidate — the other field could have policy implications."""
        mock_cache = self._run_handler(
            sender=User,
            instance=_FakeUser(),
            update_fields=["last_login", "email"],
        )
        prefix = user_app_cache_key("1")
        mock_cache.keys.assert_called_once_with(f"{prefix}/*")
        mock_cache.delete_many.assert_called_once_with([prefix])

    def test_user_save_without_update_fields_invalidates(self):
        """``update_fields=None`` means a full save — anything could have
        changed, so we invalidate the user's own entries."""
        mock_cache = self._run_handler(sender=User, instance=_FakeUser(), update_fields=None)
        prefix = user_app_cache_key("1")
        mock_cache.keys.assert_called_once_with(f"{prefix}/*")
        mock_cache.delete_many.assert_called_once_with([prefix])

    def test_concurrent_user_saves_delete_disjoint_sets(self):
        """The deadlock property: two users being saved at the same time must
        not delete any shared cache rows. Overlapping multi-row DELETEs in
        arbitrary order are what deadlocked the cache table."""
        stored = _app_access_keys(7, 70)
        deleted_per_user = []
        for pk in (7, 70):
            fake_cache = _FakeCache(stored)
            with mock.patch.object(signals, "cache", fake_cache):
                signals.invalidate_policy_cache(
                    sender=User, instance=_FakeUser(pk=pk), update_fields=None
                )
            deleted_per_user.append(set(fake_cache.deleted))
        self.assertFalse(deleted_per_user[0] & deleted_per_user[1])

    def test_group_save_still_invalidates_all_users(self):
        """A Group save can change any member's access, so the broad
        invalidation stays for non-User senders."""
        stored = _app_access_keys(7, 70)
        fake_cache = _FakeCache(stored)
        with mock.patch.object(signals, "cache", fake_cache):
            signals.invalidate_policy_cache(sender=Group, instance=object(), update_fields=None)
        self.assertCountEqual(fake_cache.deleted, _app_access_keys(7, 70))

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
        mock_cache.keys.assert_any_call(user_app_cache_key("*"))
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
        mock_cache.keys.assert_any_call(user_app_cache_key("*"))
        mock_cache.delete_many.assert_any_call(["policy-cache-key"])
