from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceImplicit(TestOpenIDConformance):

    @retry()
    def test_oidcc_implicit_certification_test_plan(self):
        self.run_test(
            "oidcc-implicit-certification-test-plan", self.test_plan_config, self.test_variant
        )
