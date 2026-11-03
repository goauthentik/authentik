from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.enterprise.requests.models import RequestRule
from authentik.enterprise.tests import enterprise_test
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id


class RequestRuleAPITests(APITestCase):
    """`RequestRuleSerializer.validate()` must require a request_flow on either the
    rule itself or the current brand, since a rule with neither can never resolve
    a flow to send a requester through."""

    def _set_brand_flow(self, flow: Flow | None):
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = flow
        brand.save()
        return brand

    @enterprise_test()
    def test_create_rejects_no_flow_anywhere(self):
        """Rule has no request_flow and the brand has none either -> rejected."""
        self._set_brand_flow(None)
        self.client.force_login(create_test_admin_user())

        res = self.client.post(
            reverse("authentik_api:requestrule-list"),
            data={"name": generate_id()},
        )
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(RequestRule.objects.filter(name__isnull=False).exists())

    @enterprise_test()
    def test_create_allowed_with_brand_flow(self):
        """Rule has no request_flow of its own, but the brand has one -> allowed."""
        self._set_brand_flow(create_test_flow())
        self.client.force_login(create_test_admin_user())

        res = self.client.post(
            reverse("authentik_api:requestrule-list"),
            data={"name": generate_id()},
        )
        self.assertEqual(res.status_code, 201, res.content)

    @enterprise_test()
    def test_create_allowed_with_own_flow(self):
        """Rule sets its own request_flow, regardless of the brand -> allowed."""
        self._set_brand_flow(None)
        self.client.force_login(create_test_admin_user())
        rule_flow = create_test_flow()

        res = self.client.post(
            reverse("authentik_api:requestrule-list"),
            data={"name": generate_id(), "request_flow": str(rule_flow.pk)},
        )
        self.assertEqual(res.status_code, 201, res.content)

    @enterprise_test()
    def test_update_rejects_clearing_flow_with_no_brand_flow(self):
        """An existing rule's own request_flow can't be cleared if the brand has none."""
        self._set_brand_flow(None)
        self.client.force_login(create_test_admin_user())
        rule = RequestRule.objects.create(name=generate_id(), request_flow=create_test_flow())

        res = self.client.patch(
            reverse("authentik_api:requestrule-detail", kwargs={"pk": rule.pk}),
            data={"request_flow": None},
        )
        self.assertEqual(res.status_code, 400, res.content)
