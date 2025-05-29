from tests.openid_conformance.generator import generate


class TestConformanceOIDCCBasicCertification(generate("oidcc-basic-certification-test-plan")):
    pass


class TestConformanceOIDCCImplicitCertification(generate("oidcc-implicit-certification-test-plan")):
    pass
