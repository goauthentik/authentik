"""Test brands"""


from django.http import HttpRequest
from django.test import TestCase

from authentik.brands.models import Brand
from authentik.brands.utils import _BRAND_RELATED_FK_FIELDS, get_brand_for_request
from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation


class TestGetBrandForRequestSelectRelated(TestCase):
    """``get_brand_for_request`` must hydrate the FK fields read on the
    request hot path so later access doesn't trigger lazy loads."""

    def setUp(self):
        Brand.objects.all().delete()
        self.flow_auth = create_test_flow(designation=FlowDesignation.AUTHENTICATION)
        self.brand = Brand.objects.create(
            domain="select-related-test.example.com",
            flow_authentication=self.flow_auth,
        )

    def _make_request(self, host: str) -> HttpRequest:
        request = HttpRequest()
        request.META["HTTP_HOST"] = host
        return request

    def test_brand_fks_are_loaded_in_single_query(self):
        """Brand FK access after ``get_brand_for_request`` must not trigger
        extra queries."""
        request = self._make_request("select-related-test.example.com")
        with self.assertNumQueries(1):
            brand = get_brand_for_request(request)
            _ = brand.flow_authentication
            _ = brand.flow_authentication.slug if brand.flow_authentication else None
            _ = brand.flow_invalidation
            _ = brand.flow_recovery
            _ = brand.flow_unenrollment
            _ = brand.flow_user_settings
            _ = brand.flow_device_code
            _ = brand.flow_lockdown
            _ = brand.default_application

    def test_brand_related_fk_list_complete(self):
        """``_BRAND_RELATED_FK_FIELDS`` covers every Flow/Application FK on
        Brand — fails loud when a new FK is added but not registered here."""
        actual_fks = {
            f.name
            for f in Brand._meta.get_fields()
            if f.many_to_one and f.related_model is not None
        }
        relevant_fks = {
            name for name in actual_fks if name.startswith("flow_") or name == "default_application"
        }
        declared = set(_BRAND_RELATED_FK_FIELDS)
        missing = relevant_fks - declared
        self.assertFalse(
            missing,
            f"Brand FK fields {missing} aren't in _BRAND_RELATED_FK_FIELDS — "
            "add them or the request hot path will incur extra queries.",
        )

    def test_brand_related_fks_all_exist_on_model(self):
        """Every entry in ``_BRAND_RELATED_FK_FIELDS`` is a real FK on Brand.
        ``select_related`` raises ``FieldError`` at first use if any entry
        is stale, which would break every request."""
        actual_fks = {
            f.name
            for f in Brand._meta.get_fields()
            if f.many_to_one and f.related_model is not None
        }
        declared = set(_BRAND_RELATED_FK_FIELDS)
        extraneous = declared - actual_fks
        self.assertFalse(
            extraneous,
            f"_BRAND_RELATED_FK_FIELDS contains {extraneous} which don't "
            f"exist on Brand (actual FKs: {sorted(actual_fks)}).",
        )
