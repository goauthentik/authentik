from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceRPInitiated(TestOpenIDConformance):

    def setUp(self):
        super().setUp()
        OAuth2Provider.objects.filter(name__startswith="oidc-conformance-").update(
            invalidation_flow=Flow.objects.get(slug="default-invalidation-flow"),
        )

    @retry()
    def test_oidcc_rp_initiated_certification_test_plan(self):
        self.run_test(
            "oidcc-rp-initiated-logout-certification-test-plan",
            self.test_plan_config,
            {
                "client_registration": "static_client",
                "response_type": "code",
            },
        )
