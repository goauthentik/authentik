from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.enterprise.pam.models import PolicyBindingModelRequestRule
from authentik.enterprise.tests.test_license import expiry_valid
from authentik.lib.generators import generate_id


class TestRequestRules(APITestCase):

    def setUp(self):
        self.user = create_test_user()
        self.user.assign_perms_to_managed_role("authentik_pam.add_policybindingmodelrequestrule")
        self.client.force_login(self.user)

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_create_rule_for_application_succeeds(self):
        License.objects.create(key=generate_id())
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        res = self.client.post(
            reverse("authentik_api:policybindingmodelrequestrule-list"),
            data={"name": generate_id(), "pbms": [str(app.pbm_uuid)]},
        )
        self.assertEqual(res.status_code, 201, res.content)

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_create_rule_for_non_application_rejected(self):
        License.objects.create(key=generate_id())
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        other_rule = PolicyBindingModelRequestRule.objects.create(name=generate_id())
        other_rule.pbms.add(app)
        res = self.client.post(
            reverse("authentik_api:policybindingmodelrequestrule-list"),
            data={"name": generate_id(), "pbms": [str(other_rule.pbm_uuid)]},
        )
        self.assertEqual(res.status_code, 400, res.content)
        body = loads(res.content.decode())
        self.assertIn("pbms", body)
