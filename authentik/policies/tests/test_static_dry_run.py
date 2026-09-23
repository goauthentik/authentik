"""Static dry-run observations across single and bulk policy engines."""

from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.engine import FilterPolicyEngine, ListPolicyEngine, PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel, PolicyEngineMode


class TestStaticDryRun(TestCase):
    """Static observations must report matches without granting or denying access."""

    def test_static_observations(self):
        user = create_test_user()
        other = create_test_user()
        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)
        user.groups.add(child)
        for engine_type in (PolicyEngine, FilterPolicyEngine, ListPolicyEngine):
            for mode in PolicyEngineMode:
                for subject in ({"user": user}, {"group": parent}):
                    for negate in (False, True):
                        with self.subTest(
                            engine=engine_type, mode=mode, subject=subject, negate=negate
                        ):
                            target = PolicyBindingModel.objects.create(policy_engine_mode=mode)
                            binding = PolicyBinding.objects.create(
                                target=target, order=0, dry_run=True, negate=negate, **subject
                            )
                            # In ALL, a failing enforced check must still deny;
                            # in ANY, a passing enforced check must still grant.
                            PolicyBinding.objects.create(
                                target=target,
                                order=1,
                                user=other if mode == PolicyEngineMode.MODE_ALL else user,
                            )
                            if engine_type is PolicyEngine:
                                passing = engine_type(target, user).build().result.passing
                            elif engine_type is FilterPolicyEngine:
                                passing = (
                                    engine_type(target, User.objects.filter(pk=user.pk))
                                    .build()
                                    .result.exists()
                                )
                            else:
                                passing = (
                                    engine_type(
                                        PolicyBindingModel.objects.filter(pk=target.pk), user
                                    )
                                    .build()
                                    .result.exists()
                                )
                            self.assertEqual(passing, mode == PolicyEngineMode.MODE_ANY)
                            event = Event.objects.get(
                                action=EventAction.POLICY_EXECUTION,
                                context__binding__pk=binding.pk.hex,
                            )
                            self.assertEqual(event.context["result"]["passing"], not negate)
                            self.assertTrue(event.context["dry_run"])
                            self.assertFalse(event.context["cached"])
                            self.assertNotIn("policy_uuid", event.context)

    def test_static_only_empty_result_and_skipped_bindings(self):
        user = create_test_user()
        for engine_type in (PolicyEngine, FilterPolicyEngine, ListPolicyEngine):
            with self.subTest(engine=engine_type):
                target = PolicyBindingModel.objects.create()
                binding = PolicyBinding.objects.create(
                    target=target, user=user, order=0, dry_run=True
                )
                PolicyBinding.objects.create(
                    target=target, user=user, order=1, dry_run=True, enabled=False
                )
                PolicyBinding.objects.create(
                    target=target,
                    user=user,
                    order=2,
                    dry_run=True,
                    expiring=True,
                    expires=now() - timedelta(seconds=1),
                )
                for empty_result in (True, False):
                    if engine_type is PolicyEngine:
                        engine = engine_type(target, user)
                    elif engine_type is FilterPolicyEngine:
                        engine = engine_type(target, User.objects.filter(pk=user.pk))
                    else:
                        engine = engine_type(PolicyBindingModel.objects.filter(pk=target.pk), user)
                    engine.empty_result = empty_result
                    result = engine.build().result
                    self.assertEqual(
                        result.passing if engine_type is PolicyEngine else result.exists(),
                        empty_result,
                    )
                events = Event.objects.filter(
                    action=EventAction.POLICY_EXECUTION,
                    context__request__obj__pk=target.pk.hex,
                )
                self.assertEqual(events.count(), 2)
                self.assertTrue(
                    all(event.context["binding"]["pk"] == binding.pk.hex for event in events)
                )

    def test_static_debug_does_not_emit_events(self):
        user = create_test_user()
        target = PolicyBindingModel.objects.create()
        binding = PolicyBinding.objects.create(target=target, user=user, order=0, dry_run=True)
        engine = PolicyEngine(target, user)
        engine.request.debug = True
        self.assertTrue(engine.build().result.passing)
        self.assertFalse(Event.objects.filter(context__binding__pk=binding.pk.hex).exists())
