from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformance3rdPartyInitLogin(TestOpenIDConformance):

    @retry()
    def test_oidcc_3rdparty_init_login_certification_test_plan(self):
        test_plan_name = "oidcc-3rdparty-init-login-certification-test-plan"
        self.test_variant = {
            "server_metadata": "discovery",
            "client_registration": "dynamic_client",
            "response_type": "code",
        }
        self.run_test(test_plan_name, self.test_plan_config)
