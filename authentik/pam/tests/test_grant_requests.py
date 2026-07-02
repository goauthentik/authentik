from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.pam.models import GrantRequest, GrantRequestTarget, PolicyBindingModelRequestRule


class GrantRequestsTests(APITestCase):

    def test_fulfill_access_user(self):
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            pbm=app,
        )
        rule.reviewers.add(reviewer)

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
        self.assertEqual(res.status_code, 204, res.content)

    def test_fulfill_access_group(self):
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            pbm=app,
        )
        group = Group.objects.create(name=generate_id())
        group.users.add(reviewer)
        rule.reviewer_groups.add(group)

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
        self.assertEqual(res.status_code, 204, res.content)

    def test_fulfill_access_none(self):
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            pbm=app,
        )

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
