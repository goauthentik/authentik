from django.urls import reverse
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
