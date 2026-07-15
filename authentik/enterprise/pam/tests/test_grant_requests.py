from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.pam.models import (
    GrantRequest,
    GrantRequestApproval,
    GrantRequestTarget,
    PolicyBindingModelRequestRule,
    RequestStatus,
)
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class GrantRequestsTests(APITestCase):

    def test_fulfill_access_user(self):
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)
        rule.reviewers.add(reviewer)

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
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer)
        rule.reviewer_groups.add(group)

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
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)

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
        reviewer_a.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer_a.assign_perms_to_managed_role("authentik_pam.view_grantrequest")
        reviewer_b = create_test_user()
        reviewer_b.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer_b.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        rule.pbms.add(app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer_a, reviewer_b)
        rule.reviewer_groups.add(group)

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
        reviewer_a.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer_a.assign_perms_to_managed_role("authentik_pam.view_grantrequest")
        reviewer_b = create_test_user()
        reviewer_b.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer_b.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        rule.pbms.add(app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer_a, reviewer_b)
        rule.reviewer_groups.add(group)

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
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            min_reviewers=2,
        )
        rule.pbms.add(app)
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer)
        rule.reviewer_groups.add(group)

        req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        for _ in range(2):
            res = self.client.patch(
                reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
                data={"status": "approved", "data": {}},
            )
            self.assertEqual(res.status_code, 204, res.content)
        self.assertEqual(GrantRequestApproval.objects.filter(request=req).count(), 1)

    def test_revoke_active_grant(self):
        """A reviewer can revoke an approved (active) grant, expiring its PolicyBinding"""
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)
        rule.reviewers.add(reviewer)

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

        res = self.client.post(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.REVOKED)
        self.assertEqual(req.revoked_by, reviewer)
        self.assertFalse(req.is_active)

        binding = PolicyBinding.objects.get(user=requester, target=app)
        self.assertTrue(binding.is_expired)

    def test_revoke_requires_reviewer_permission(self):
        """A user who isn't an eligible reviewer for the rule cannot revoke"""
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")
        outsider = create_test_user()
        outsider.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        outsider.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)
        rule.reviewers.add(reviewer)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
        )

        self.client.force_login(outsider)
        res = self.client.post(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 400)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)

    def test_revoke_before_approval_is_noop(self):
        """Revoking a request that was never approved does nothing"""
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        rule.pbms.add(app)
        rule.reviewers.add(reviewer)

        req = GrantRequest.objects.create(created_by=create_test_user())
        GrantRequestTarget.objects.create(request=req, target=app)

        self.client.force_login(reviewer)
        res = self.client.post(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk}),
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)
