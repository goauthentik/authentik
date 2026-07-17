"""SCIM Application Policies tests"""

from unittest.mock import patch

from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding, PolicyEngineMode
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.tenants.models import Tenant


class SCIMApplicationPoliciesTests(TestCase):
    """SCIM Application Policies tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as to only have the test users and groups
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        Tenant.objects.update(avatars="none")

        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)

        self.group1 = Group.objects.create(name="group-1")
        self.group2 = Group.objects.create(name="group-2")
        self.group3 = Group.objects.create(name="group-3")

        self.users = {}
        for i in range(1, 5):
            uid = generate_id()
            self.users[i] = User.objects.create(
                username=uid,
                name=f"{uid} User",
                email=f"{uid}@goauthentik.io",
            )

        self.users[1].ak_groups.add(self.group1)
        self.users[2].ak_groups.add(self.group2)
        self.users[4].ak_groups.add(self.group1)
        self.users[4].ak_groups.add(self.group2)

    def test_no_group_policy(self):
        """Test with no group policy set"""
        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[3].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_single_group_policy(self):
        """Test with one group policy set"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_multiple_group_policies(self):
        """Test with multiple group policies set"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)
        PolicyBinding.objects.create(target=self.app, group=self.group2, order=0)

        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_user_binding(self):
        """Test with a direct user binding (no group, no policy)"""
        PolicyBinding.objects.create(target=self.app, user=self.users[3], order=0)

        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[3].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_user_and_group_binding_mode_any(self):
        """Test with mixed user + group bindings, MODE_ANY (default)"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)
        PolicyBinding.objects.create(target=self.app, user=self.users[3], order=1)

        user_qs = self.provider.get_object_qs(User)

        # Users 1, 4 in group1 + user 3 directly bound
        self.assertEqual(
            set([self.users[1].pk, self.users[3].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_negated_group_binding(self):
        """Test with a negated group binding (block users in group1)"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, negate=True, order=0)

        user_qs = self.provider.get_object_qs(User)

        # Users NOT in group1: user 2 (group2 only) and user 3 (no groups)
        # Users 1 and 4 are excluded because they're in group1
        self.assertEqual(
            set([self.users[2].pk, self.users[3].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_hierarchical_group_binding(self):
        """Test that group binding includes users in descendant groups (via group.parents)"""
        # Make group1 a parent of group2: users in group2 should match a binding on group1
        self.group2.parents.add(self.group1)

        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        user_qs = self.provider.get_object_qs(User)

        # User 1: directly in group1 -> match
        # User 2: in group2 (descendant of group1) -> match
        # User 3: no groups -> no match
        # User 4: in group1 and group2 -> match
        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_mode_all_two_group_bindings(self):
        """MODE_ALL: user must be in ALL bound groups to sync"""
        self.app.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.app.save()

        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)
        PolicyBinding.objects.create(target=self.app, group=self.group2, order=1)

        user_qs = self.provider.get_object_qs(User)

        # Only user 4 is in BOTH group1 AND group2
        self.assertEqual(
            set([self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_disabled_binding_ignored(self):
        """Disabled bindings should not affect the queryset"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, enabled=False, order=0)

        user_qs = self.provider.get_object_qs(User)

        # Disabled binding -> treated like no bindings -> all users sync
        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[3].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_no_bindings_respects_app_access_without_bindings_flag(self):
        """When the tenant flag ``AppAccessWithoutBindings`` is False, an
        application with no bindings must yield zero in-scope users."""
        # Default (True): all users in scope (covered by test_no_group_policy)
        # Now flip the flag and verify no users are in scope
        with patch.object(AppAccessWithoutBindings, "get", return_value=False):
            user_qs = self.provider.get_object_qs(User)
            self.assertEqual(set(user_qs.values_list("pk", flat=True)), set())

    def test_static_bindings_dont_invoke_policy_engine_per_user(self):
        """Performance regression test for the per-user PolicyEngine evaluation
        in :meth:`get_object_qs`.

        When the application's bindings are purely static (group/user, no Policy
        object), ``get_object_qs`` must filter via SQL and NOT instantiate
        ``PolicyEngine`` per user. The previous implementation iterated every
        user in the database and built a ``PolicyEngine`` per user, which on a
        production instance with thousands of users multiplied across paginated
        sync tasks produced hundreds of thousands of PolicyEngine evaluations
        per provider per full sync.
        """
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        # Add a few more users to make any per-user iteration obvious
        for _ in range(20):
            uid = generate_id()
            user = User.objects.create(username=uid, name=uid, email=f"{uid}@goauthentik.io")
            user.groups.add(self.group1)

        with patch("authentik.policies.engine.PolicyEngine") as mock_policy_engine:
            list(self.provider.get_object_qs(User))

        self.assertEqual(
            mock_policy_engine.call_count,
            0,
            (
                f"PolicyEngine was instantiated {mock_policy_engine.call_count} times "
                "during get_object_qs(). Static bindings (no Policy object) must be "
                "evaluated as a single SQL filter, not per-user."
            ),
        )

    def test_static_bindings_query_count_independent_of_user_count(self):
        """Performance regression test: query count for ``get_object_qs`` must
        not scale with the number of users in the database.

        Construction issues O(1) queries (one to fetch the application's
        bindings); materialization is one further query. Crucially, neither
        count grows with the user count -- the previous implementation ran a
        PolicyEngine evaluation per user, multiplying the query count by the
        user count.
        """
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        # Baseline with the existing 4 users
        with CaptureQueriesContext(connection) as ctx_small:
            list(self.provider.get_object_qs(User))
        baseline_queries = len(ctx_small.captured_queries)

        # Add many more users to the same group
        for _ in range(50):
            uid = generate_id()
            user = User.objects.create(username=uid, name=uid, email=f"{uid}@goauthentik.io")
            user.groups.add(self.group1)

        with CaptureQueriesContext(connection) as ctx_large:
            list(self.provider.get_object_qs(User))

        self.assertEqual(
            len(ctx_large.captured_queries),
            baseline_queries,
            (
                f"Query count grew from {baseline_queries} to "
                f"{len(ctx_large.captured_queries)} after adding 50 users. "
                "Query count must be O(1) with respect to user count for "
                "static bindings."
            ),
        )

    def test_actual_policy_binding_falls_back_to_per_user_evaluation(self):
        """When a real ``Policy`` is bound, we cannot translate it to SQL and
        must fall back to per-user evaluation. Verify correctness is preserved
        on the slow path (this test does NOT assert performance)."""
        policy = DummyPolicy.objects.create(name=generate_id(), result=True, wait_min=0, wait_max=1)
        PolicyBinding.objects.create(target=self.app, policy=policy, order=0)

        user_qs = self.provider.get_object_qs(User)

        # Policy passes for everyone -> all users sync
        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[3].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_mixed_static_and_policy_binding_mode_all_prefilters(self):
        """When MODE_ALL is set with both a static binding and a real policy,
        the static binding is used as a SQL pre-filter to shrink the candidate
        set before per-user policy evaluation."""
        self.app.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.app.save()

        # Static binding restricts to group1 (users 1, 4)
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)
        # Policy that always passes
        policy = DummyPolicy.objects.create(name=generate_id(), result=True, wait_min=0, wait_max=1)
        PolicyBinding.objects.create(target=self.app, policy=policy, order=1)

        user_qs = self.provider.get_object_qs(User)

        # MODE_ALL: must pass both static (in group1) AND policy (always True)
        # -> users 1 and 4
        self.assertEqual(
            set([self.users[1].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )
