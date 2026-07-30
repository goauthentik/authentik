from authentik.providers.oauth2.models import IssuerMode, OAuth2Provider
from tests.decorators import retry
from tests.live import SSLLiveMixin
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceConfig(TestOpenIDConformance, SSLLiveMixin):

    def setUp(self):
        super().setUp()
        OAuth2Provider.objects.filter(name__startswith="oidc-conformance-").update(
            issuer_mode=IssuerMode.PER_PROVIDER
        )

    @retry()
    def test_oidcc_config_certification_test_plan(self):
        self.run_test(
            "oidcc-config-certification-test-plan",
            {
                "alias": "authentik",
                "description": "authentik",
                "server": {
                    "discoveryUrl": self.url(
                        "authentik_providers_oauth2:provider-info",
                        application_slug="oidc-conformance-1",
                    ),
                },
            },
        )
