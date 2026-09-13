"""ListPolicyEngine tests"""

from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.engine import ListPolicyEngine, PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel, PolicyEngineMode
from authentik.policies.tests.test_process import clear_policy_cache


class TestListPolicyEngine(TestCase):
    """ListPolicyEngine tests"""

    def setUp(self):
        clear_policy_cache()
        self.policy_true = DummyPolicy.objects.create(
            name=generate_id(), result=True, wait_min=0, wait_max=1
        )
        self.group_a = Group.objects.create(name=generate_id())
        self.group_b = Group.objects.create(name=generate_id())
        self.user = create_test_user()
        self.user.groups.add(self.group_a)
        self.obj_a = PolicyBindingModel.objects.create()
        self.obj_b = PolicyBindingModel.objects.create()
        self.obj_c = PolicyBindingModel.objects.create()
        self.objs = PolicyBindingModel.objects.filter(
            pk__in=[self.obj_a.pk, self.obj_b.pk, self.obj_c.pk]
        )

    def test_list_engine_empty(self):
        """No bindings at all on any object -> empty_result decides"""
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk},
        )

        engine = ListPolicyEngine(self.objs, self.user)
        engine.empty_result = False
        self.assertEqual(set(engine.build().result.values_list("pk", flat=True)), set())

    def test_list_engine_static_group_any(self):
        """MODE_ANY static group binding, evaluated independently per object"""
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        PolicyBinding.objects.create(target=self.obj_b, group=self.group_b, order=0)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_c.pk},
        )

    def test_list_engine_static_group_all(self):
        """MODE_ALL with two group bindings on one object: only passes if user is in both"""
        self.obj_a.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.obj_a.save()
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_b, order=1)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_b.pk, self.obj_c.pk},
        )

    def test_list_engine_static_user_binding(self):
        """Direct user binding"""
        other_user = create_test_user()
        PolicyBinding.objects.create(target=self.obj_a, user=self.user, order=0)
        PolicyBinding.objects.create(target=self.obj_b, user=other_user, order=0)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_c.pk},
        )

    def test_list_engine_negate(self):
        """Negated group binding excludes members instead of including them"""
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, negate=True, order=0)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_b.pk, self.obj_c.pk},
        )

    def test_list_engine_group_hierarchy(self):
        """A binding on a parent group also matches a user only in a descendant group"""
        group_parent = Group.objects.create(name=generate_id())
        self.group_a.parents.add(group_parent)
        PolicyBinding.objects.create(target=self.obj_a, group=group_parent, order=0)
        PolicyBinding.objects.create(target=self.obj_b, group=self.group_b, order=0)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_c.pk},
        )

    def test_list_engine_policy_fallback(self):
        """Real Policy bindings on different objects fall back to per-object evaluation
        and are evaluated independently."""
        policy_false = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=0, wait_max=1
        )
        PolicyBinding.objects.create(target=self.obj_a, policy=self.policy_true, order=0)
        PolicyBinding.objects.create(target=self.obj_b, policy=policy_false, order=0)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_c.pk},
        )

    def test_list_engine_mode_all_static_prefilter_skips_dynamic(self):
        """MODE_ALL: a failing static binding must skip dynamic evaluation for that
        object entirely."""
        self.obj_a.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.obj_a.save()
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_b, order=0)
        PolicyBinding.objects.create(target=self.obj_a, policy=self.policy_true, order=1)
        with patch(
            "authentik.policies.dummy.models.DummyPolicy.passes",
            side_effect=AssertionError("dynamic policy should not be evaluated"),
        ):
            engine = ListPolicyEngine(self.objs, self.user)
            result = set(engine.build().result.values_list("pk", flat=True))
        self.assertEqual(result, {self.obj_b.pk, self.obj_c.pk})

    def test_list_engine_mode_all_mixed_passes(self):
        """MODE_ALL with a passing static binding and a passing dynamic binding passes overall"""
        self.obj_a.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.obj_a.save()
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        PolicyBinding.objects.create(target=self.obj_a, policy=self.policy_true, order=1)
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk},
        )

    def test_list_engine_expired_static_binding_ignored(self):
        """An expired static binding is excluded from evaluation entirely"""
        self.obj_a.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.obj_a.save()
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        PolicyBinding.objects.create(
            target=self.obj_a,
            group=self.group_b,
            order=1,
            expiring=True,
            expires=now() - timedelta(minutes=10),
        )
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk},
        )

    def test_list_engine_expired_policy_binding_ignored(self):
        """An expired real-Policy binding is excluded from evaluation entirely, even
        though (were it not expired) it would force MODE_ALL to fail."""
        policy_false = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=0, wait_max=1
        )
        self.obj_a.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.obj_a.save()
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        PolicyBinding.objects.create(
            target=self.obj_a,
            policy=policy_false,
            order=1,
            expiring=True,
            expires=now() - timedelta(minutes=10),
        )
        engine = ListPolicyEngine(self.objs, self.user)
        self.assertEqual(
            set(engine.build().result.values_list("pk", flat=True)),
            {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk},
        )

    def test_list_engine_static_query_count_independent_of_object_count(self):
        """Query count for the static-only path must not scale with the number of
        objects."""
        objs = [PolicyBindingModel.objects.create() for _ in range(50)]
        for obj in objs:
            PolicyBinding.objects.create(target=obj, group=self.group_a, order=0)
        qs = PolicyBindingModel.objects.filter(pk__in=[o.pk for o in objs])
        engine = ListPolicyEngine(qs, self.user)
        with CaptureQueriesContext(connections["default"]) as ctx:
            result = set(engine.build().result.values_list("pk", flat=True))
        self.assertLess(ctx.final_queries, 20)
        self.assertEqual(result, {o.pk for o in objs})

    def test_list_engine_dynamic_query_count_independent_of_object_count(self):
        """The slow (per-object Policy) path must not re-fetch bindings, the static
        aggregate, the cache, or the polymorphic `policy`/`target` FKs per object --
        query count must stay O(1) regardless of the number of objects."""
        small_objs = [PolicyBindingModel.objects.create() for _ in range(3)]
        for obj in small_objs:
            PolicyBinding.objects.create(target=obj, group=self.group_a, order=0)
            PolicyBinding.objects.create(target=obj, policy=self.policy_true, order=1)
        small_qs = PolicyBindingModel.objects.filter(pk__in=[o.pk for o in small_objs])

        ListPolicyEngine(small_qs, self.user).build()  # warm cache
        with CaptureQueriesContext(connections["default"]) as ctx_small:
            list(ListPolicyEngine(small_qs, self.user).build().result)
        baseline_queries = len(ctx_small.captured_queries)

        extra_objs = [PolicyBindingModel.objects.create() for _ in range(50)]
        for obj in extra_objs:
            PolicyBinding.objects.create(target=obj, group=self.group_a, order=0)
            PolicyBinding.objects.create(target=obj, policy=self.policy_true, order=1)
        large_qs = PolicyBindingModel.objects.filter(pk__in=[o.pk for o in small_objs + extra_objs])

        ListPolicyEngine(large_qs, self.user).build()  # warm cache
        with CaptureQueriesContext(connections["default"]) as ctx_large:
            list(ListPolicyEngine(large_qs, self.user).build().result)

        self.assertLessEqual(
            len(ctx_large.captured_queries),
            baseline_queries + 2,
            (
                f"Query count grew from {baseline_queries} to "
                f"{len(ctx_large.captured_queries)} after adding {len(extra_objs)} objects "
                "-- bindings/cache/static-resolution/FK lookups are being repeated per object."
            ),
        )

    def test_list_engine_no_policy_engine_instantiated_for_static_path(self):
        """Purely static bindings must never instantiate a per-object PolicyEngine."""
        PolicyBinding.objects.create(target=self.obj_a, group=self.group_a, order=0)
        with patch("authentik.policies.engine.PolicyEngine") as mock_engine:
            engine = ListPolicyEngine(self.objs, self.user)
            list(engine.build().result)
        self.assertEqual(mock_engine.call_count, 0)

    def test_list_engine_bulk_cache_prefetch_single_round_trip(self):
        """The slow (per-object Policy) path must fetch cache entries via a single
        cache.get_many() call instead of one cache.get() per (binding, object) pair."""
        objs = [PolicyBindingModel.objects.create() for _ in range(3)]
        for obj in objs:
            PolicyBinding.objects.create(target=obj, policy=self.policy_true, order=0)
        qs = PolicyBindingModel.objects.filter(pk__in=[o.pk for o in objs])

        with (
            patch(
                "authentik.policies.engine.cache.get_many", wraps=cache.get_many
            ) as mock_get_many,
            patch("authentik.policies.engine.cache.get", wraps=cache.get) as mock_get,
        ):
            engine = ListPolicyEngine(qs, self.user)
            result = set(engine.build().result.values_list("pk", flat=True))

        self.assertEqual(result, {o.pk for o in objs})
        mock_get_many.assert_called_once()
        mock_get.assert_not_called()

    def test_list_engine_cache_reused_across_builds(self):
        """A second ListPolicyEngine.build() must reuse the PolicyResults cached by the
        first build (bulk-prefetched via one cache.get_many()) instead of re-evaluating
        the (slow, per-object) DummyPolicy again."""
        PolicyBinding.objects.create(target=self.obj_a, policy=self.policy_true, order=0)

        first = set(
            ListPolicyEngine(self.objs, self.user).build().result.values_list("pk", flat=True)
        )
        self.assertEqual(first, {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk})

        with (
            patch(
                "authentik.policies.engine.cache.get_many", wraps=cache.get_many
            ) as mock_get_many,
            patch(
                "authentik.policies.dummy.models.DummyPolicy.passes",
                side_effect=AssertionError("policy should be served from cache, not re-evaluated"),
            ),
        ):
            engine = ListPolicyEngine(self.objs, self.user)
            second = set(engine.build().result.values_list("pk", flat=True))

        self.assertEqual(second, {self.obj_a.pk, self.obj_b.pk, self.obj_c.pk})
        mock_get_many.assert_called_once()

    def test_list_engine_http_request_enriched_once(self):
        """set_http_request() (context/geoip enrichment) must be called exactly once
        per build(), not once per object -- the fixed user/http_request means one
        enriched PolicyRequest can be reused across every object."""
        objs = [PolicyBindingModel.objects.create() for _ in range(5)]
        for obj in objs:
            PolicyBinding.objects.create(target=obj, policy=self.policy_true, order=0)
        qs = PolicyBindingModel.objects.filter(pk__in=[o.pk for o in objs])
        http_request = RequestFactory().get("/")
        http_request.user = self.user

        with patch(
            "authentik.policies.engine.PolicyRequest.set_http_request", autospec=True
        ) as mock_set:
            engine = ListPolicyEngine(qs, self.user, http_request)
            engine.build()
        mock_set.assert_called_once()

    def test_list_engine_matches_single_object_engine(self):
        """Cross-validate ListPolicyEngine's static-binding handling (negate, group
        hierarchy, MODE_ALL/MODE_ANY) against the per-object PolicyEngine (the source
        of truth), for a fixed user across a batch of objects.

        This asserts *agreement* with PolicyEngine rather than hand-computed expected
        sets, so it can't be wrong in the same way as the implementation being tested.
        """
        group_parent = Group.objects.create(name=generate_id())
        group_child = Group.objects.create(name=generate_id())
        group_child.parents.add(group_parent)
        group_other = Group.objects.create(name=generate_id())

        user = create_test_user()
        user.groups.add(group_child)

        scenarios = [
            (
                "negate group (with hierarchy)",
                PolicyEngineMode.MODE_ANY,
                [{"group": group_parent, "negate": True}],
            ),
            (
                "negate user",
                PolicyEngineMode.MODE_ANY,
                [{"user": user, "negate": True}],
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
                    {"user": user, "negate": True},
                ],
            ),
        ]

        objs = []
        for message, mode, binding_specs in scenarios:
            pbm = PolicyBindingModel.objects.create(policy_engine_mode=mode)
            for idx, spec in enumerate(binding_specs):
                PolicyBinding.objects.create(target=pbm, order=idx, **spec)
            objs.append((message, pbm))

        qs = PolicyBindingModel.objects.filter(pk__in=[pbm.pk for _, pbm in objs])
        engine = ListPolicyEngine(qs, user)
        batch_passing = set(engine.build().result.values_list("pk", flat=True))

        for message, pbm in objs:
            with self.subTest(message):
                single = PolicyEngine(pbm, user)
                single.use_cache = False
                expected = single.build().passing
                self.assertEqual(
                    pbm.pk in batch_passing,
                    expected,
                    f"{message}: mismatch",
                )
