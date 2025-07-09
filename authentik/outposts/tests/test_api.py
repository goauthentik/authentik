"""Test outpost service connection API"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from django.test import Client

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.outposts.api.outposts import OutpostSerializer
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostType, default_outpost_config, ProxySession
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.proxy.models import ProxyProvider
from django.utils import timezone
from datetime import timedelta
from authentik.outposts.tasks import proxy_session_cleanup


class TestOutpostServiceConnectionsAPI(APITestCase):
    """Test outpost service connection API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name=generate_id(), expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    @reconcile_app("authentik_outposts")
    def test_managed_name_change(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"name": ["Embedded outpost's name cannot be changed"]}
        )

    @reconcile_app("authentik_outposts")
    def test_managed_without_managed(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        embedded_outpost.managed = ""
        embedded_outpost.save()
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 200)
        embedded_outpost.refresh_from_db()
        self.assertEqual(embedded_outpost.managed, MANAGED_OUTPOST)

    def test_outpost_validation(self):
        """Test Outpost validation"""
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    ProxyProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertTrue(valid.is_valid())
        invalid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    LDAPProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("providers", invalid.errors)

    def test_types(self):
        """Test OutpostServiceConnections's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:outpostserviceconnection-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_outpost_config(self):
        """Test Outpost's config field"""
        provider = ProxyProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        invalid = OutpostSerializer(
            data={"name": generate_id(), "providers": [provider.pk], "config": ""}
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("config", invalid.errors)
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "providers": [provider.pk],
                "config": default_outpost_config(generate_id()),
                "type": OutpostType.PROXY,
            }
        )
        self.assertTrue(valid.is_valid())


def test_proxysession_expiry_cleanup(db):
    provider = None
    # Create a ProxySession that is already expired
    expired = ProxySession.objects.create(
        session_key="expired-key",
        data=b"test",
        claims={},
        redirect="",
        expires=timezone.now() - timedelta(days=1),
        expiring=True,
        provider=provider,
    )
    # Create a ProxySession that is not expired
    valid = ProxySession.objects.create(
        session_key="valid-key",
        data=b"test",
        claims={},
        redirect="",
        expires=timezone.now() + timedelta(days=1),
        expiring=True,
        provider=provider,
    )
    # ExpiringModel's default manager should filter out expired
    sessions = ProxySession.objects.all()
    assert valid in sessions
    assert expired not in sessions
    # Expired session should be deleted by cleanup
    ProxySession.objects.cleanup_expired()
    assert not ProxySession.objects.filter(pk=expired.pk).exists()


def test_proxysession_admin_crud(db):
    User = get_user_model()
    admin_user = User.objects.create_superuser(username="admin", password="admin", email="admin@example.com")
    client = Client()
    client.login(username="admin", password="admin")
    # Create via admin
    add_url = reverse("admin:outposts_proxysession_add")
    data = {
        "session_key": "admin-key",
        "data": b"test",
        "claims": "{}",
        "redirect": "",
        "expires_0": "2099-01-01",
        "expires_1": "00:00:00",
        "expiring": True,
        "provider": "",
    }
    response = client.post(add_url, data, follow=True)
    assert response.status_code == 200
    # List view
    list_url = reverse("admin:outposts_proxysession_changelist")
    response = client.get(list_url)
    assert b"admin-key" in response.content
    # Delete via admin
    obj = ProxySession.objects.get(session_key="admin-key")
    delete_url = reverse("admin:outposts_proxysession_delete", args=[obj.pk])
    response = client.post(delete_url, {"post": "yes"}, follow=True)
    assert response.status_code == 200
    assert not ProxySession.objects.filter(session_key="admin-key").exists()


def test_proxysession_django_cleanup(db):
    """Test that Django's cleanup_expired method properly removes expired sessions"""
    provider = None
    # Create a ProxySession that is already expired
    expired = ProxySession.objects.create(
        session_key="expired-key-django",
        data=b"test",
        claims={},
        redirect="",
        expires=timezone.now() - timedelta(days=1),
        expiring=True,
        provider=provider,
    )
    # Create a ProxySession that is not expired
    valid = ProxySession.objects.create(
        session_key="valid-key-django",
        data=b"test",
        claims={},
        redirect="",
        expires=timezone.now() + timedelta(days=1),
        expiring=True,
        provider=provider,
    )
    
    # Run the cleanup task
    count = proxy_session_cleanup()
    
    # Verify that only the expired session was deleted
    assert count == 1
    assert not ProxySession.objects.filter(pk=expired.pk).exists()
    assert ProxySession.objects.filter(pk=valid.pk).exists()
