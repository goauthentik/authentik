"""Test used_by delete actions"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.used_by import DeleteAction
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice


class TestUsedBy(APITestCase):
    def test_protected_relation(self):
        """Objects that block the deletion aren't reported as deleted with it"""
        user = create_test_admin_user()
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(), client_id=generate_id(), api_hostname=generate_id()
        )
        DuoDevice.objects.create(user=user, stage=stage, duo_user_id=generate_id())
        self.client.force_login(user)
        response = self.client.get(
            reverse("authentik_api:authenticatorduostage-used-by", kwargs={"pk": stage.pk})
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            [entry["action"] for entry in response.json()], [DeleteAction.PROTECT.value]
        )
