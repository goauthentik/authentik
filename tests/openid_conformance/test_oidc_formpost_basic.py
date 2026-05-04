from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceFormPostBasic(TestOpenIDConformance):

    @retry()
    def test_oidcc_formpost_basic_certification_test_plan(self):
        self.run_test(
            "oidcc-formpost-basic-certification-test-plan",
            self.test_plan_config,
            {
                "server_metadata": "discovery",
                "client_registration": "static_client",
            },
        )
