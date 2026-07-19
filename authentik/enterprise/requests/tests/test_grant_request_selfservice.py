from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.requests.models import (
    GrantRequest,
    GrantRequestTarget,
    RequestRule,
    RequestRuleBinding,
    RequestStatus,
)
from authentik.enterprise.requests.stage import GrantRequestFinalStageView
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class GrantRequestsSelfServiceTests(APITestCase):
    """Requesters and reviewers should be able to use the API against their own
    requests without needing any explicitly, globally-assigned RBAC permission."""

    def test_create_without_explicit_permission(self):
        """Any authenticated user can kick off a request, without request_grantrequest"""
        requester = create_test_user()
        self.client.force_login(requester)

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=requester, order=0)

        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.STAGE_CONFIGURATION,
        )
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = flow
        brand.save()

        res = self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": [str(app.pk)]},
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn("link", res.json())

    def test_list_only_shows_own_requests(self):
        """A requester only sees requests they created (and were granted
        object-level access to, as `GrantRequestFinalStageView` does on creation)"""
        requester = create_test_user()
        other_user = create_test_user()

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        own_req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=own_req, target=app)
        requester.assign_perms_to_managed_role("authentik_requests.view_grantrequest", own_req)

        other_req = GrantRequest.objects.create(created_by=other_user)
        GrantRequestTarget.objects.create(request=other_req, target=app)
        other_user.assign_perms_to_managed_role("authentik_requests.view_grantrequest", other_req)

        self.client.force_login(requester)
        res = self.client.get(reverse("authentik_api:grantrequest-list"))
        self.assertEqual(res.status_code, 200, res.content)
        content = res.json()
        pks = {result["uuid"] for result in content["results"]}
        self.assertEqual(pks, {str(own_req.pk)})

    def test_cancel_pending_request(self):
        """A requester can cancel (delete) their own still-pending request"""
        requester = create_test_user()
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)
        requester.assign_perms_to_managed_role(
            ["authentik_requests.view_grantrequest", "authentik_requests.delete_grantrequest"], req
        )

        self.client.force_login(requester)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-detail", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 204, res.content)
        self.assertFalse(GrantRequest.objects.filter(pk=req.pk).exists())

    def test_cancel_non_pending_request_rejected(self):
        """A requester cannot cancel a request that's already been fulfilled"""
        requester = create_test_user()
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        req = GrantRequest.objects.create(created_by=requester, status=RequestStatus.APPROVED)
        GrantRequestTarget.objects.create(request=req, target=app)
        requester.assign_perms_to_managed_role(
            ["authentik_requests.view_grantrequest", "authentik_requests.delete_grantrequest"], req
        )

        self.client.force_login(requester)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-detail", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 400)
        self.assertTrue(GrantRequest.objects.filter(pk=req.pk).exists())

    def test_reviewer_gets_object_permission_on_creation(self):
        """Reviewers eligible for a rule attached to a request's targets are
        automatically granted object-level access to that request, without any
        pre-existing RBAC grant, while an unrelated user still gets none."""
        reviewer = create_test_user()
        requester = create_test_user()
        outsider = create_test_user()

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        GrantRequestFinalStageView._assign_permissions([rule], req)

        self.client.force_login(reviewer)
        res = self.client.get(reverse("authentik_api:grantrequest-detail", kwargs={"pk": req.pk}))
        self.assertEqual(res.status_code, 200, res.content)

        res = self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )
        self.assertEqual(res.status_code, 204, res.content)

        self.client.force_login(outsider)
        res = self.client.get(reverse("authentik_api:grantrequest-detail", kwargs={"pk": req.pk}))
        self.assertEqual(res.status_code, 403, res.content)

    def test_pending_review_lists_only_for_eligible_reviewer(self):
        """`pending_review` shows a pending request to an eligible reviewer, and
        excludes it for an unrelated user and for a non-pending request."""
        reviewer = create_test_user()
        outsider = create_test_user()

        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)

        pending_req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=pending_req, target=app)

        fulfilled_req = GrantRequest.objects.create(
            created_by=create_test_user(), status=RequestStatus.APPROVED
        )
        GrantRequestTarget.objects.create(request=fulfilled_req, target=app)

        self.client.force_login(reviewer)
        res = self.client.get(reverse("authentik_api:grantrequest-pending-review"))
        self.assertEqual(res.status_code, 200, res.content)
        pks = {result["uuid"] for result in res.json()["results"]}
        self.assertEqual(pks, {str(pending_req.pk)})

        self.client.force_login(outsider)
        res = self.client.get(reverse("authentik_api:grantrequest-pending-review"))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["results"], [])
