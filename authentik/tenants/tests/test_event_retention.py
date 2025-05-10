"""Test event retention"""

from django.test.client import RequestFactory
from django_tenants.utils import get_public_schema_name
from rest_framework.test import APITestCase

from authentik.common.utils.time import timedelta_from_string
from authentik.events.models import Event, EventAction
from authentik.tenants.models import Tenant


class TestEventRetention(APITestCase):
    """Test event retention"""

    def test_event_retention(self):
        """Test brand's event retention"""
        default_tenant = Tenant.objects.get(schema_name=get_public_schema_name())
        default_tenant.event_retention = "weeks=3"
        default_tenant.save()
        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = default_tenant
        event = Event.new(action=EventAction.SYSTEM_EXCEPTION, message="test").from_http(request)
        self.assertEqual(event.expires.day, (event.created + timedelta_from_string("weeks=3")).day)
        self.assertEqual(
            event.expires.month,
            (event.created + timedelta_from_string("weeks=3")).month,
        )
        self.assertEqual(
            event.expires.year, (event.created + timedelta_from_string("weeks=3")).year
        )
