from tests.e2e.utils import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceImplicit(TestOpenIDConformance):

    @retry()
    def test_oidcc_implicit_certification_test_plan(self):
        test_plan_name = "oidcc-implicit-certification-test-plan"
        self.run_test(test_plan_name, self.test_plan_config)
