from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceBasic(TestOpenIDConformance):

    @retry()
    def test_oidcc_basic_certification_test(self):
        self.run_test(
            "oidcc-basic-certification-test-plan", self.test_plan_config, self.test_variant
        )
