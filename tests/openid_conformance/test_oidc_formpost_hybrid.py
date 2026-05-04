from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceFormPostHybrid(TestOpenIDConformance):

    @retry()
    def test_oidcc_formpost_hybrid_certification_test_plan(self):
        self.run_test(
            "oidcc-formpost-hybrid-certification-test-plan",
            self.test_plan_config,
            {
                "server_metadata": "discovery",
                "client_registration": "static_client",
            },
        )
