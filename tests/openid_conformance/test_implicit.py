from tests.e2e.utils import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceBasic(TestOpenIDConformance):

    @retry()
    def test_oidcc_basic_certification_test(self):
        test_plan_name = "oidcc-basic-certification-test-plan"
        self.run_test(test_plan_name, self.test_plan_config)
