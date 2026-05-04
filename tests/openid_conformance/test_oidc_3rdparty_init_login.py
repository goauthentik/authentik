from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformance3rdPartyInitLogin(TestOpenIDConformance):

    @retry()
    def test_oidcc_3rdparty_init_login_certification_test_plan(self):
        self.run_test(
            "oidcc-3rdparty-init-login-certification-test-plan",
            self.test_plan_config,
            {
                "response_type": "code",
            },
        )
