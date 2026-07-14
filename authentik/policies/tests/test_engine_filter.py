"""policy engine tests"""

from unittest.mock import patch

from django.core.cache import cache
from django.db import connections
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.engine import FilterPolicyEngine, PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel, PolicyEngineMode
from authentik.policies.tests.test_process import clear_policy_cache


class TestFilterPolicyEngine(TestCase):
    """FilterPolicyEngine tests"""

    def setUp(self):
        clear_policy_cache()
        self.policy_true = DummyPolicy.objects.create(
            name=generate_id(), result=True, wait_min=0, wait_max=1
        )
        self.group_a = Group.objects.create(name=generate_id())
        self.group_b = Group.objects.create(name=generate_id())
        self.user_a = create_test_user()
        self.user_b = create_test_user()
        self.user_c = create_test_user()
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)
        self.users = User.objects.filter(pk__in=[self.user_a.pk, self.user_b.pk, self.user_c.pk])

    def test_multi_engine_empty(self):
        """No bindings at all -> empty_result decides"""
        pbm = PolicyBindingModel.objects.create()
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_a.pk, self.user_b.pk, self.user_c.pk},
        )

        engine = FilterPolicyEngine(pbm, self.users)
        engine.empty_result = False
        self.assertEqual(set(engine.build().result.values_list("pk", flat=True)), set())

    def test_multi_engine_static_group_any(self):
        """MODE_ANY static group binding"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, group=self.group_a, order=0)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_a.pk, self.user_b.pk},
        )

    def test_multi_engine_static_group_all(self):
        """MODE_ALL with two group bindings: only members of both pass"""
        pbm = PolicyBindingModel.objects.create(policy_engine_mode=PolicyEngineMode.MODE_ALL)
        PolicyBinding.objects.create(target=pbm, group=self.group_a, order=0)
        PolicyBinding.objects.create(target=pbm, group=self.group_b, order=1)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_b.pk},
        )

    def test_multi_engine_static_user_binding(self):
        """Direct user binding"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, user=self.user_c, order=0)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_c.pk},
        )

    def test_multi_engine_negate(self):
        """Negated group binding excludes members instead of including them"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, group=self.group_a, negate=True, order=0)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_c.pk},
        )

    def test_multi_engine_group_hierarchy(self):
        """A binding on a parent group also matches users only in a descendant group"""
        group_parent = Group.objects.create(name=generate_id())
        self.group_b.parents.add(group_parent)
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, group=group_parent, order=0)
        engine = FilterPolicyEngine(pbm, self.users)
        # user_b is in group_b, a descendant of group_parent
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_b.pk},
        )

    def test_multi_engine_policy_fallback(self):
        """Real Policy bindings can't be translated to SQL and fall back to per-user
        PolicyEngine evaluation; correctness must be preserved on this slow path."""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=0)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_a.pk, self.user_b.pk, self.user_c.pk},
        )

    def test_multi_engine_mixed_static_and_policy_mode_all_prefilters(self):
        """MODE_ALL with a static binding and a real policy: static binding restricts
        the candidate set before per-user policy evaluation."""
        pbm = PolicyBindingModel.objects.create(policy_engine_mode=PolicyEngineMode.MODE_ALL)
        PolicyBinding.objects.create(target=pbm, group=self.group_a, order=0)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=1)
        engine = FilterPolicyEngine(pbm, self.users)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.user_a.pk, self.user_b.pk},
        )

    def test_multi_engine_static_query_count_independent_of_user_count(self):
        """Query count for the static-only path must not scale with the number of
        bindings or users -- it must be evaluated as a single SQL filter."""
        pbm = PolicyBindingModel.objects.create()
        for x in range(1000):
            PolicyBinding.objects.create(target=pbm, order=x, group=self.group_a)
        engine = FilterPolicyEngine(pbm, self.users)
        with CaptureQueriesContext(connections["default"]) as ctx:
            result = set(engine.build().result.values_list("pk", flat=True))
        self.assertLess(ctx.final_queries, 1000)
        self.assertEqual(result, {self.user_a.pk, self.user_b.pk})

    def test_multi_engine_no_policy_engine_instantiated_for_static_path(self):
        """Purely static bindings must never instantiate a per-user PolicyEngine."""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, group=self.group_a, order=0)
        with patch("authentik.policies.engine.PolicyEngine") as mock_engine:
            engine = FilterPolicyEngine(pbm, self.users)
            list(engine.build().result)
        self.assertEqual(mock_engine.call_count, 0)

    def test_negate_matches_single_user_engine(self):
        """Cross-validate FilterPolicyEngine's negated static-binding handling against
        the per-user PolicyEngine (the source of truth for negate semantics), across
        group hierarchy, user bindings, and MODE_ALL/MODE_ANY combinations.

        This asserts *agreement* with PolicyEngine rather than hand-computed expected
        sets, so it can't be wrong in the same way as the implementation being tested.
        """
        group_parent = Group.objects.create(name=generate_id())
        group_child = Group.objects.create(name=generate_id())
        group_child.parents.add(group_parent)
        group_other = Group.objects.create(name=generate_id())

        user_top = create_test_user()  # member of group_parent directly
        user_leaf = create_test_user()  # member of group_child only (descendant of parent)
        user_other = create_test_user()  # member of group_other only
        user_none = create_test_user()  # no groups
        user_multi = create_test_user()  # member of group_child and group_other

        user_top.groups.add(group_parent)
        user_leaf.groups.add(group_child)
        user_other.groups.add(group_other)
        user_multi.groups.add(group_child)
        user_multi.groups.add(group_other)

        all_users = [user_top, user_leaf, user_other, user_none, user_multi]
        users_qs = User.objects.filter(pk__in=[u.pk for u in all_users])

        scenarios = [
            (
                "negate group (with hierarchy)",
                PolicyEngineMode.MODE_ANY,
                [{"group": group_parent, "negate": True}],
            ),
            (
                "negate user",
                PolicyEngineMode.MODE_ANY,
                [{"user": user_leaf, "negate": True}],
            ),
            (
                "MODE_ALL negate + positive",
                PolicyEngineMode.MODE_ALL,
                [{"group": group_parent, "negate": True}, {"group": group_other}],
            ),
            (
                "MODE_ANY negate + positive",
                PolicyEngineMode.MODE_ANY,
                [{"group": group_parent, "negate": True}, {"group": group_other}],
            ),
            (
                "multiple negated bindings, MODE_ALL",
                PolicyEngineMode.MODE_ALL,
                [
                    {"group": group_parent, "negate": True},
                    {"user": user_other, "negate": True},
                ],
            ),
            (
                "multiple negated bindings, MODE_ANY",
                PolicyEngineMode.MODE_ANY,
                [
                    {"group": group_parent, "negate": True},
                    {"user": user_other, "negate": True},
                ],
            ),
        ]

        for message, mode, binding_specs in scenarios:
            with self.subTest(message):
                pbm = PolicyBindingModel.objects.create(policy_engine_mode=mode)
                for idx, spec in enumerate(binding_specs):
                    PolicyBinding.objects.create(target=pbm, order=idx, **spec)

                engine = FilterPolicyEngine(pbm, users_qs)
                batch_passing = set(engine.build().result.values_list("pk", flat=True))

                for user in all_users:
                    single = PolicyEngine(pbm, user)
                    single.use_cache = False
                    expected = single.build().passing
                    self.assertEqual(
                        user.pk in batch_passing,
                        expected,
                        f"{message}: mismatch for user {user.pk}",
                    )

    def test_bulk_cache_prefetch_single_round_trip(self):
        """The slow (per-user Policy) path must fetch cache entries via a single
        cache.get_many() call instead of one cache.get() per (binding, user) pair."""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=0)

        with (
            patch(
                "authentik.policies.engine.cache.get_many", wraps=cache.get_many
            ) as mock_get_many,
            patch("authentik.policies.engine.cache.get", wraps=cache.get) as mock_get,
        ):
            engine = FilterPolicyEngine(pbm, self.users)
            result = set(engine.build().result.values_list("pk", flat=True))

        self.assertEqual(result, {self.user_a.pk, self.user_b.pk, self.user_c.pk})
        mock_get_many.assert_called_once()
        mock_get.assert_not_called()

    def test_cache_reused_across_builds(self):
        """A second FilterPolicyEngine.build() must reuse the PolicyResults cached by
        the first build (bulk-prefetched via one cache.get_many()) instead of
        re-evaluating the (slow, per-user) DummyPolicy again."""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=0)

        # First build populates the cache (real DummyPolicy evaluation happens).
        first = set(FilterPolicyEngine(pbm, self.users).build().result.values_list("pk", flat=True))
        self.assertEqual(first, {self.user_a.pk, self.user_b.pk, self.user_c.pk})

        with (
            patch(
                "authentik.policies.engine.cache.get_many", wraps=cache.get_many
            ) as mock_get_many,
            patch(
                "authentik.policies.dummy.models.DummyPolicy.passes",
                side_effect=AssertionError("policy should be served from cache, not re-evaluated"),
            ),
        ):
            engine = FilterPolicyEngine(pbm, self.users)
            second = set(engine.build().result.values_list("pk", flat=True))

        self.assertEqual(second, {self.user_a.pk, self.user_b.pk, self.user_c.pk})
        mock_get_many.assert_called_once()
