from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceFormPostHybrid(TestOpenIDConformance):

    @retry()
    def test_oidcc_formpost_hybrid_certification_test_plan(self):
        test_plan_name = "oidcc-formpost-hybrid-certification-test-plan"
        self.test_variant = {
            "server_metadata": "discovery",
            "client_registration": "static_client",
            "response_type": "code id_token",
            "response_mode": "form_post",
        }
        self.run_test(test_plan_name, self.test_plan_config)
