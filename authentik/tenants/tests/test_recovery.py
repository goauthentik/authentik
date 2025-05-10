"""Test Tenant Recovery API"""

from json import loads

from django.urls import reverse
from django_tenants.utils import get_public_schema_name

from authentik.common.config import CONFIG
from authentik.core.models import Token, TokenIntents, User
from authentik.crypto.generators import generate_id
from authentik.tenants.models import Tenant
from authentik.tenants.tests.utils import TenantAPITestCase

TENANTS_API_KEY = generate_id()
HEADERS = {"Authorization": f"Bearer {TENANTS_API_KEY}"}


class TestRecovery(TenantAPITestCase):
    """Test recovery endpoints"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.get(schema_name=get_public_schema_name())
        self.user: User = User.objects.create_user(username="recovery-test-user")

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_recovery_admin_group(self):
        """Test creation of admin group"""
        response = self.client.post(
            reverse(
                "authentik_api:tenant-create-admin-group",
                args=[self.tenant.tenant_uuid],
            ),
            data={"user": self.user.username},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_superuser)

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_recovery_admin_group_invalid(self):
        """Test invalid creation of admin group"""
        response = self.client.post(
            reverse(
                "authentik_api:tenant-create-admin-group",
                args=[self.tenant.tenant_uuid],
            ),
            data={"user": "invalid"},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 404)

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_create_key(self):
        """Test creation of a new key"""
        response = self.client.post(
            reverse(
                "authentik_api:tenant-create-recovery-key",
                args=[self.tenant.tenant_uuid],
            ),
            data={"user": self.user.username, "duration_days": 365},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, body["url"])
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 1)

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_create_key_invalid(self):
        """Test creation of a new key (invalid)"""
        response = self.client.post(
            reverse(
                "authentik_api:tenant-create-recovery-key",
                args=[self.tenant.tenant_uuid],
            ),
            data={"user": "invalid", "duration_days": 365},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 0)
