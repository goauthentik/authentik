from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2LogoutMethod, OAuth2Provider
from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceFrontchannel(TestOpenIDConformance):

    def setUp(self):
        super().setUp()
        OAuth2Provider.objects.filter(name__startswith="oidc-conformance-").update(
            invalidation_flow=Flow.objects.get(slug="default-invalidation-flow"),
            logout_method=OAuth2LogoutMethod.FRONTCHANNEL,
            logout_uri="https://localhost:8443/test/a/authentik/frontchannel_logout",
        )

    @retry()
    def test_oidcc_frontchannel_logout_certification_test_plan(self):
        self.run_test(
            "oidcc-frontchannel-rp-initiated-logout-certification-test-plan",
            self.test_plan_config,
            {
                "client_registration": "static_client",
                "response_type": "code",
            },
        )
