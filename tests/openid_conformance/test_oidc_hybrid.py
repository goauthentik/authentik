from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceHybrid(TestOpenIDConformance):

    @retry()
    def test_oidcc_hybrid_certification_test_plan(self):
        self.run_test(
            "oidcc-hybrid-certification-test-plan",
            self.test_plan_config,
            {
                "server_metadata": "discovery",
                "client_registration": "static_client",
            },
        )
