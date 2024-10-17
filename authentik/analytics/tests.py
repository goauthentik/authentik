"""authentik analytics tests"""

from json import loads
from requests_mock import Mocker

from django.test import TestCase
from django.urls import reverse

from authentik import __version__
from authentik.analytics.tasks import send_analytics
from authentik.analytics.utils import get_analytics_apps_data, get_analytics_apps_description, get_analytics_data, get_analytics_description, get_analytics_models_data, get_analytics_models_description
from authentik.core.models import Group, User
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.tenants.utils import get_current_tenant


class TestAnalytics(TestCase):
    """test analytics api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.client.force_login(self.user)
        self.tenant = get_current_tenant()

    def test_description_api(self):
        """Test Version API"""
        response = self.client.get(reverse("authentik_api:analytics-description-list"))
        self.assertEqual(response.status_code, 200)
        loads(response.content)

    def test_data_api(self):
        """Test Version API"""
        response = self.client.get(reverse("authentik_api:analytics-data-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["data"]["version"], __version__)

    def test_sending_enabled(self):
        """Test analytics sending"""
        self.tenant.analytics_enabled = True
        self.tenant.save()
        with Mocker() as mocker:
            mocker.post("https://customers.goauthentik.io/api/analytics/post/", status_code=200)
            send_analytics.delay().get()
            self.assertTrue(
                Event.objects.filter(
                    action=EventAction.ANALYTICS_SENT
                ).exists()
            )

    def test_sending_disabled(self):
        """Test analytics sending"""
        self.tenant.analytics_enabled = False
        self.tenant.save()
        send_analytics.delay().get()
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.ANALYTICS_SENT
            ).exists()
        )

    def test_description_data_match_apps(self):
        """Test description and data keys match"""
        description = get_analytics_apps_description()
        data = get_analytics_apps_data()
        self.assertEqual(data.keys(), description.keys())

    def test_description_data_match_models(self):
        """Test description and data keys match"""
        description = get_analytics_models_description()
        data = get_analytics_models_data()
        self.assertEqual(data.keys(), description.keys())
