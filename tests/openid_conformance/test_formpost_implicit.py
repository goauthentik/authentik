from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceFormPostImplicit(TestOpenIDConformance):

    @retry()
    def test_oidcc_formpost_implicit_certification_test_plan(self):
        test_plan_name = "oidcc-formpost-implicit-certification-test-plan"
        self.run_test(test_plan_name, self.test_plan_config)
