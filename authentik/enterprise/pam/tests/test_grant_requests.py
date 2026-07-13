from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.pam.models import (
    Grant,
    GrantRequest,
    GrantRequestTarget,
    Persona,
    PersonaTemplate,
    PolicyBindingModelRequestRule,
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

    def test_fulfill_access_persona(self):
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

        requester = create_test_user()
        persona = Persona.create_for_user(generate_id(), requester)

        req = GrantRequest.objects.create(
            created_by=requester,
            persona=persona,
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
        self.assertTrue(Grant.objects.filter(persona=persona, target=app).exists())
        self.assertTrue(PolicyBinding.objects.filter(user=persona, target=app).exists())
        self.assertFalse(PolicyBinding.objects.filter(user=requester, target=app).exists())

    def test_fulfill_instantiate_persona_template(self):
        """Requesting a PersonaTemplate self-instantiates a Persona for the requester"""
        reviewer = create_test_user()
        reviewer.assign_perms_to_managed_role("authentik_pam.change_grantrequest")
        reviewer.assign_perms_to_managed_role("authentik_pam.view_grantrequest")

        template = PersonaTemplate.objects.create(name=generate_id())
        rule = PolicyBindingModelRequestRule.objects.create(
            name=generate_id(),
            pbm=template,
        )
        rule.reviewers.add(reviewer)

        requester = create_test_user()
        req = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req, target=template)

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
        persona = Persona.objects.filter(template=template, parent=requester).first()
        self.assertIsNotNone(persona)

        # A second approved request for the same template shouldn't create a duplicate persona
        req2 = GrantRequest.objects.create(created_by=requester)
        GrantRequestTarget.objects.create(request=req2, target=template)
        res2 = self.client.patch(
            reverse(
                "authentik_api:grantrequest-fulfill",
                kwargs={
                    "pk": req2.pk,
                },
            ),
            data={
                "status": "approved",
                "data": {},
            },
        )
        self.assertEqual(res2.status_code, 204, res2.content)
        self.assertEqual(Persona.objects.filter(template=template, parent=requester).count(), 1)
