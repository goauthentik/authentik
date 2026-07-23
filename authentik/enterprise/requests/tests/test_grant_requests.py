from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.requests.models import (
    GrantRequest,
    GrantRequestApproval,
    GrantRequestTarget,
    RequestRule,
    RequestRuleBinding,
    RequestStatus,
)
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class GrantRequestsTests(APITestCase):

    def _grant_perms(self, user):
        user.assign_perms_to_managed_role("authentik_requests.view_grantrequest")
        user.assign_perms_to_managed_role("authentik_requests.fulfill_grantrequest")
        user.assign_perms_to_managed_role("authentik_requests.revoke_grantrequest")

    def test_fulfill_access_user(self):
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(
            created_by=requester,
        )
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)

        res = self.client.patch(
            reverse(
                "authentik_api:grantrequest-fulfill",
                kwargs={
                    "pk": req.pk,
                },
            ),
            data={
                "status": "approved",
                "data": {},
            },
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.assertTrue(PolicyBinding.objects.filter(user=requester, target=app).exists())

    def test_fulfill_approval_fires_event(self):
        """Approving a request emits an ACCESS_REQUEST_APPROVED event"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.ACCESS_REQUEST_APPROVED,
                context__model__pk=req.pk.hex,
            ).exists()
        )

    def test_fulfill_access_group(self):
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer)
        PolicyBinding.objects.create(target=rule, group=group, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(
            created_by=requester,
        )
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)

        res = self.client.patch(
            reverse(
                "authentik_api:grantrequest-fulfill",
                kwargs={
                    "pk": req.pk,
                },
            ),
            data={
                "status": "approved",
                "data": {},
            },
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.assertTrue(PolicyBinding.objects.filter(user=requester, target=app).exists())

    def test_fulfill_access_none(self):
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        # reviewer has no PolicyBinding relation to the rule at all

        req = GrantRequest.objects.create(
            created_by=create_test_user(),
        )
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)

        res = self.client.patch(
            reverse(
                "authentik_api:grantrequest-fulfill",
                kwargs={
                    "pk": req.pk,
                },
            ),
            data={
                "status": "approved",
                "data": {},
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_fulfill_rejects_self_approval(self):
        """A requester who is also an eligible reviewer for the rule cannot fulfill
        (approve or deny) their own request"""
        requester = create_test_user()
        self._grant_perms(requester)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=requester, order=0)

        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(requester)

        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 400)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)
        self.assertFalse(PolicyBinding.objects.filter(user=requester, target=app).exists())

    def test_fulfill_min_reviewers_requires_multiple_approvals(self):
        """A rule with min_reviewers=2 must not grant access after only one approval"""
        reviewer_a = create_test_user()
        self._grant_perms(reviewer_a)
        reviewer_b = create_test_user()
        self._grant_perms(reviewer_b)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        RequestRuleBinding.objects.create(rule=rule, target=app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer_a, reviewer_b)
        PolicyBinding.objects.create(target=rule, group=group, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer_a)
        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)
        self.assertFalse(PolicyBinding.objects.filter(user=requester, target=app).exists())

        self.client.force_login(reviewer_b)
        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.assertTrue(PolicyBinding.objects.filter(user=requester, target=app).exists())

    def test_fulfill_denial_overrides_pending_approvals(self):
        """A single denial finalizes the request even if min_reviewers hasn't been reached"""
        reviewer_a = create_test_user()
        self._grant_perms(reviewer_a)
        reviewer_b = create_test_user()
        self._grant_perms(reviewer_b)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        RequestRuleBinding.objects.create(rule=rule, target=app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer_a, reviewer_b)
        PolicyBinding.objects.create(target=rule, group=group, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer_a)
        self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )

        self.client.force_login(reviewer_b)
        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "denied", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.DENIED)
        self.assertFalse(PolicyBinding.objects.filter(user=requester, target=app).exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.ACCESS_REQUEST_DENIED,
                context__model__pk=req.pk.hex,
            ).exists()
        )

    def test_fulfill_repeated_approval_is_idempotent(self):
        """Approving twice as the same reviewer must not create duplicate approval rows"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)
        other_group_member = create_test_user()

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        RequestRuleBinding.objects.create(rule=rule, target=app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer, other_group_member)
        PolicyBinding.objects.create(target=rule, group=group, order=0)

        req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        for _ in range(2):
            res = self.client.patch(
                reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
                data={"status": "approved", "data": {}},
            )
            self.assertEqual(res.status_code, 204, res.content)

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)
        self.assertEqual(GrantRequestApproval.objects.filter(request=req).count(), 1)

    def test_fulfill_grant_expiry_uses_requested_expiry(self):
        """The granted PolicyBinding's expiry comes from requested_expiry (resolved at
        request-creation time), not from the request's own (pending) expires"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(
            created_by=requester,
            expiring=True,
            expires=now() + timedelta(hours=6),
            requested_expiry="minutes=10",
        )
        GrantRequestTarget.objects.create(request=req, target=app)

        before = now()
        self.client.force_login(reviewer)
        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)

        binding = PolicyBinding.objects.get(user=requester, target=app)
        self.assertTrue(binding.expiring)
        self.assertGreater(binding.expires, before + timedelta(minutes=9))
        self.assertLess(binding.expires, before + timedelta(minutes=11))

    def test_revoke_active_grant(self):
        """A reviewer can revoke an approved (active) grant, expiring its PolicyBinding"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        req.refresh_from_db()
        self.assertTrue(req.is_active)

        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.REVOKED)
        self.assertEqual(req.revoked_by, reviewer)
        self.assertFalse(req.is_active)

        binding = PolicyBinding.objects.including_expired().get(user=requester, target=app)
        self.assertTrue(binding.is_expired)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.ACCESS_REQUEST_REVOKED,
                context__model__pk=req.pk.hex,
            ).exists()
        )

    def test_revoke_requires_reviewer_permission(self):
        """A user who isn't an eligible reviewer for the rule cannot revoke"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)
        outsider = create_test_user()
        self._grant_perms(outsider)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )

        self.client.force_login(outsider)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 400)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)

    def test_revoke_before_approval_is_noop(self):
        """Revoking a request that was never approved does nothing"""
        reviewer = create_test_user()
        self._grant_perms(reviewer)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)


class GrantRequestCreateFlowSelectionTests(APITestCase):
    """`create()` should prefer a request flow shared by every rule that granted
    access to the requested pbms, falling back to the brand's default otherwise."""

    def _set_brand_flow(self, flow: Flow | None):
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = flow
        brand.save()
        return brand

    def _make_flow(self) -> Flow:
        return Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.STAGE_CONFIGURATION,
        )

    def test_create_uses_shared_rule_flow_over_brand(self):
        """When the (single) granting rule has its own request_flow, prefer it."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_flow = self._make_flow()
        rule = RequestRule.objects.create(name=generate_id(), request_flow=rule_flow)
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)

        brand_flow = self._make_flow()
        self._set_brand_flow(brand_flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn(rule_flow.slug, res.json()["link"])
        self.assertNotIn(brand_flow.slug, res.json()["link"])

    def test_create_falls_back_to_brand_when_rule_has_no_flow(self):
        """When the granting rule has no request_flow set, fall back to the brand's."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)

        brand_flow = self._make_flow()
        self._set_brand_flow(brand_flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn(brand_flow.slug, res.json()["link"])

    def test_create_falls_back_to_brand_when_rules_disagree(self):
        """Two pbms granted by two rules with different request_flows must not agree
        on a shared flow, so the brand's is used instead."""
        requester = create_test_user()
        self.client.force_login(requester)

        app_a = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_a_flow = self._make_flow()
        rule_a = RequestRule.objects.create(name=generate_id(), request_flow=rule_a_flow)
        rule_a_binding = RequestRuleBinding.objects.create(rule=rule_a, target=app_a)
        PolicyBinding.objects.create(target=rule_a_binding, user=requester, order=0)

        app_b = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_b_flow = self._make_flow()
        rule_b = RequestRule.objects.create(name=generate_id(), request_flow=rule_b_flow)
        rule_b_binding = RequestRuleBinding.objects.create(rule=rule_b, target=app_b)
        PolicyBinding.objects.create(target=rule_b_binding, user=requester, order=0)

        brand_flow = self._make_flow()
        self._set_brand_flow(brand_flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app_a.pk), str(app_b.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn(brand_flow.slug, res.json()["link"])

    def test_create_uses_shared_flow_across_multiple_pbms(self):
        """Two pbms granted by rules that DO share the same request_flow should use it."""
        requester = create_test_user()
        self.client.force_login(requester)

        shared_flow = self._make_flow()

        app_a = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_a = RequestRule.objects.create(name=generate_id(), request_flow=shared_flow)
        rule_a_binding = RequestRuleBinding.objects.create(rule=rule_a, target=app_a)
        PolicyBinding.objects.create(target=rule_a_binding, user=requester, order=0)

        app_b = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_b = RequestRule.objects.create(name=generate_id(), request_flow=shared_flow)
        rule_b_binding = RequestRuleBinding.objects.create(rule=rule_b, target=app_b)
        PolicyBinding.objects.create(target=rule_b_binding, user=requester, order=0)

        brand_flow = self._make_flow()
        self._set_brand_flow(brand_flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app_a.pk), str(app_b.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn(shared_flow.slug, res.json()["link"])

    def test_create_404_when_no_flow_available(self):
        """No rule flow and no brand flow -> 404, not a crash."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)

        self._set_brand_flow(None)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)]},
        )
        self.assertEqual(res.status_code, 404)


class GrantRequestCreateExpiryResolutionTests(APITestCase):
    """`create()` should resolve the pending/max expiry from the granting
    RequestRuleBinding(s), taking the strictest value when several apply."""

    def _set_brand_flow(self, flow: Flow | None):
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = flow
        brand.save()
        return brand

    def _make_flow(self) -> Flow:
        return Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.STAGE_CONFIGURATION,
        )

    def _run_flow(self, flow: Flow):
        """Follow through to the flow executor, exactly as the frontend does when it
        opens the `link` returned by `create()`, so the in-memory final stage runs."""
        return self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )

    def test_create_resolves_pending_and_max_expiry_from_binding(self):
        """The created GrantRequest's pending expiry, and its resolved grant expiry
        (absent any override), come from the granting RequestRuleBinding rather than
        a fixed value."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(
            rule=rule,
            target=app,
            expiry_pending="minutes=15",
            expiry_granted_max="minutes=20",
        )
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)
        flow = self._make_flow()
        self._set_brand_flow(flow)

        before = now()
        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self._run_flow(flow)

        req = GrantRequest.objects.get(targets=app)
        self.assertEqual(req.requested_expiry, "minutes=20")
        self.assertGreater(req.expires, before + timedelta(minutes=14))
        self.assertLess(req.expires, before + timedelta(minutes=16))

    def test_create_takes_strictest_expiry_across_multiple_bindings(self):
        """When two rules grant access to the two requested pbms with different
        expiry configs, the stricter (shorter) value wins for both pending and max."""
        requester = create_test_user()
        self.client.force_login(requester)

        app_a = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_a = RequestRule.objects.create(name=generate_id())
        binding_a = RequestRuleBinding.objects.create(
            rule=rule_a, target=app_a, expiry_pending="hours=2", expiry_granted_max="hours=2"
        )
        PolicyBinding.objects.create(target=binding_a, user=requester, order=0)

        app_b = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_b = RequestRule.objects.create(name=generate_id())
        binding_b = RequestRuleBinding.objects.create(
            rule=rule_b,
            target=app_b,
            expiry_pending="minutes=10",
            expiry_granted_max="minutes=5",
        )
        PolicyBinding.objects.create(target=binding_b, user=requester, order=0)

        flow = self._make_flow()
        self._set_brand_flow(flow)

        before = now()
        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app_a.pk), str(app_b.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self._run_flow(flow)

        req = GrantRequest.objects.filter(targets=app_a).filter(targets=app_b).get()
        self.assertEqual(req.requested_expiry, "minutes=5")
        self.assertGreater(req.expires, before + timedelta(minutes=9))
        self.assertLess(req.expires, before + timedelta(minutes=11))

    def test_create_accepts_expiry_override_within_max(self):
        """A requester-supplied `expiry` override shorter than the binding's max is
        honored, resolved once the flow's final stage runs."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(
            rule=rule, target=app, expiry_granted_max="hours=1"
        )
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)
        flow = self._make_flow()
        self._set_brand_flow(flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)], "expiry": "minutes=5"},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self._run_flow(flow)

        req = GrantRequest.objects.get(targets=app)
        self.assertEqual(req.requested_expiry, "minutes=5")

    def test_create_clamps_expiry_override_to_max(self):
        """A requester-supplied `expiry` override longer than the binding's max is
        clamped down, enforced by GrantRequestFinalStageView once the flow completes."""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(
            rule=rule, target=app, expiry_granted_max="minutes=10"
        )
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)
        flow = self._make_flow()
        self._set_brand_flow(flow)

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)], "expiry": "hours=5"},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self._run_flow(flow)

        req = GrantRequest.objects.get(targets=app)
        self.assertEqual(req.requested_expiry, "minutes=10")

    def test_create_rejects_malformed_expiry_override(self):
        """An unparsable `expiry` override is rejected at request-creation time"""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)
        self._set_brand_flow(self._make_flow())

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)], "expiry": "not-a-duration"},
        )
        self.assertEqual(res.status_code, 400)
