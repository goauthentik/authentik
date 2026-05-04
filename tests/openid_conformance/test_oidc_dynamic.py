from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceDynamic(TestOpenIDConformance):

    @retry()
    def test_oidcc_dynamic_certification_test_plan(self):
        self.run_test(
            "oidcc-dynamic-certification-test-plan",
            self.test_plan_config,
            {
                "response_type": "code",
            },
        )
