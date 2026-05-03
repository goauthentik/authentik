from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceDynamic(TestOpenIDConformance):

    @retry()
    def test_oidcc_dynamic_certification_test_plan(self):
        test_plan_name = "oidcc-dynamic-certification-test-plan"
        self.test_variant = {
            "response_type": "code",
        }
        self.run_test(test_plan_name, self.test_plan_config)
