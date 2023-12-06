"""Test Settings API"""
from json import loads

from django.urls import reverse
from django_tenants.utils import get_public_schema_name

from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.tenants.models import Domain, Tenant
from authentik.tenants.tests.utils import TenantAPITestCase

TENANTS_API_KEY = generate_id()
HEADERS = {"Authorization": f"Bearer {TENANTS_API_KEY}"}


# class TestSettingsAPI(TenantAPITestCase):
#     def setUp(self):
#         super().setUp()
#         self.tenant_1 = Tenant.objects.get(schema_name=get_public_schema_name())
#         self.tenant_2 = Tenant.objects.create(
#             name=generate_id(), schema_name="t_" + generate_id().lower()
#         )
#
#     @CONFIG.patch("outposts.disable_embedded_outpost", True)
#     @CONFIG.patch("tenants.enabled", True)
#     @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
#     def test_domain(self):
#         """Test domain creation"""
#         response = self.client.post(
#             reverse("authentik_api:domain-list"),
#             headers=HEADERS,
#             data={"tenant": self.tenant.pk, "domain": "test.domain"},
#         )
#         self.assertEqual(response.status_code, 201)
#         body = loads(response.content.decode())
#         self.assertEqual(self.tenant.domains.get(domain="test.domain").pk, body["id"])
#         self.assertEqual(self.tenant.domains.get(domain="test.domain").is_primary, True)
#
#         response = self.client.post(
#             reverse("authentik_api:domain-list"),
#             headers=HEADERS,
#             data={"tenant": self.tenant.pk, "domain": "newprimary.domain", "is_primary": True},
#         )
#         self.assertEqual(response.status_code, 201)
#         self.assertEqual(
#             Domain.objects.get(tenant=self.tenant, domain="newprimary.domain").is_primary, True
#         )
#         self.assertEqual(
#             Domain.objects.get(tenant=self.tenant, domain="test.domain").is_primary, False
#         )
