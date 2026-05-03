from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceHybrid(TestOpenIDConformance):

    @retry()
    def test_oidcc_hybrid_certification_test_plan(self):
        test_plan_name = "oidcc-hybrid-certification-test-plan"
        self.test_variant = {
            "server_metadata": "discovery",
            "client_registration": "static_client",
            "response_type": "code id_token",
        }
        self.run_test(test_plan_name, self.test_plan_config)
