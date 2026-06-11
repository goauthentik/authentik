"""Tests for ``authentik.policies.signals.invalidate_policy_cache``.

Regression guards for the per-login cache-invalidation skip. ``last_login``-
only User saves must not trigger the broad ``cache.keys(...)`` invalidation.
"""

from unittest import TestCase, mock


class _FakeUser:
    pk = 1


class _FakePolicy:
    pk = "fake-policy-pk"


class TestInvalidatePolicyCacheSkipsLastLoginOnly(TestCase):
    """The handler must NOT touch the cache when a User save is purely a
    ``last_login`` update."""

    def _run_handler(self, sender, instance, update_fields):
        """Run the handler with mocked cache/PolicyBinding; return the
        cache mock for assertions."""
        from authentik.policies import signals

        with (
            mock.patch.object(signals, "cache") as mock_cache,
            mock.patch.object(signals, "PolicyBinding") as mock_pb,
        ):
            mock_cache.keys.return_value = []
            mock_pb.objects.filter.return_value = []
            signals.invalidate_policy_cache(
                sender=sender,
                instance=instance,
                update_fields=update_fields,
            )
            return mock_cache

    def test_user_save_with_only_last_login_does_not_invalidate(self):
        """User save with update_fields=["last_login"] is the per-login hot
        path. The handler must short-circuit without touching the cache."""
        from authentik.core.models import User

        mock_cache = self._run_handler(
            sender=User, instance=_FakeUser(), update_fields=["last_login"]
        )
        mock_cache.keys.assert_not_called()
        mock_cache.delete_many.assert_not_called()

    def test_user_save_with_last_login_as_set_does_not_invalidate(self):
        """``update_fields`` may be a set (Django supports any iterable).
        The handler must treat ``{"last_login"}`` identically to
        ``["last_login"]``."""
        from authentik.core.models import User

        mock_cache = self._run_handler(
            sender=User, instance=_FakeUser(), update_fields={"last_login"}
        )
        mock_cache.keys.assert_not_called()

    def test_user_save_with_other_fields_still_invalidates(self):
        """A User save that updates ``email`` (or any non-last_login field)
        must still invalidate the cache — those updates can affect policy
        evaluation, group membership computation, etc."""
        from authentik.core.models import User

        mock_cache = self._run_handler(sender=User, instance=_FakeUser(), update_fields=["email"])
        mock_cache.keys.assert_called()
        mock_cache.delete_many.assert_called()

    def test_user_save_with_last_login_plus_other_fields_invalidates(self):
        """If ``update_fields`` contains ``last_login`` plus anything else,
        we must invalidate — the other field could have policy implications."""
        from authentik.core.models import User

        mock_cache = self._run_handler(
            sender=User,
            instance=_FakeUser(),
            update_fields=["last_login", "email"],
        )
        mock_cache.keys.assert_called()

    def test_user_save_without_update_fields_invalidates(self):
        """``update_fields=None`` means a full save — anything could have
        changed, so we conservatively invalidate."""
        from authentik.core.models import User

        mock_cache = self._run_handler(sender=User, instance=_FakeUser(), update_fields=None)
        mock_cache.keys.assert_called()

    def test_policy_save_still_invalidates(self):
        """Non-User senders are unaffected by the new short-circuit.
        Policy/PolicyBinding/PolicyBindingModel/Group saves must continue to
        invalidate as before — those changes affect access decisions for
        every user."""
        from authentik.policies.models import Policy

        mock_cache = self._run_handler(
            sender=Policy,
            instance=_FakePolicy(),
            update_fields=["last_login"],  # irrelevant — sender isn't User
        )
        mock_cache.keys.assert_called()
        mock_cache.delete_many.assert_called()
