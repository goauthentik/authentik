from unittest.mock import PropertyMock, patch

from rest_framework.test import APITestCase

from authentik.endpoints.controller import BaseController, Capabilities
from authentik.endpoints.models import Connector
from authentik.endpoints.tasks import endpoints_sync
from authentik.lib.generators import generate_id


class TestEndpointTasks(APITestCase):
    def test_agent_sync(self):
        class controller(BaseController):
            def capabilities(self):
                return [Capabilities.ENROLL_AUTOMATIC_API]

        with patch.object(Connector, "controller", PropertyMock(return_value=controller)):
            connector = Connector.objects.create(name=generate_id())
            self.assertEqual(len(connector.schedule_specs), 1)

            endpoints_sync.send(connector.pk).get_result(block=True)

    def test_agent_no_sync(self):
        class controller(BaseController):
            def capabilities(self):
                return []

        with patch.object(Connector, "controller", PropertyMock(return_value=controller)):
            connector = Connector.objects.create(name=generate_id())
            self.assertEqual(len(connector.schedule_specs), 0)

            endpoints_sync.send(connector.pk).get_result(block=True)
