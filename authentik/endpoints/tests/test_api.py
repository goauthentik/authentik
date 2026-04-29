from unittest.mock import PropertyMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.controller import BaseController
from authentik.endpoints.models import StageMode
from authentik.lib.generators import generate_id


class TestAPI(APITestCase):
    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_endpoint_stage_agent(self):
        connector = AgentConnector.objects.create(name=generate_id())
        res = self.client.post(
            reverse("authentik_api:stages-endpoint-list"),
            data={
                "name": generate_id(),
                "connector": str(connector.pk),
                "mode": StageMode.REQUIRED,
            },
        )
        self.assertEqual(res.status_code, 201)

    def test_endpoint_stage_agent_no_stage(self):
        connector = AgentConnector.objects.create(name=generate_id())

        class controller(BaseController):
            def capabilities(self):
                return []

        with patch.object(AgentConnector, "controller", PropertyMock(return_value=controller)):
            res = self.client.post(
                reverse("authentik_api:stages-endpoint-list"),
                data={
                    "name": generate_id(),
                    "connector": str(connector.pk),
                    "mode": StageMode.REQUIRED,
                },
            )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"connector": ["Selected connector is not compatible with this stage."]}
        )
