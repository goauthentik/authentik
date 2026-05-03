from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceConfig(TestOpenIDConformance):

    @retry()
    def test_oidcc_config_certification_test_plan(self):
        test_plan_name = "oidcc-config-certification-test-plan"
        self.test_variant = {}
        self.run_test(test_plan_name, self.test_plan_config)
