from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.lib.generators import generate_id
from tests.decorators import retry
from tests.live import SSLLiveMixin
from tests.openid_conformance.base import TestOpenIDConformance


class TestOpenIDConformanceSSFTransmitter(TestOpenIDConformance, SSLLiveMixin):

    def setUp(self):
        super().setUp()
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=CertificateKeyPair.objects.get(name="authentik Self-signed Certificate"),
            backchannel_application=Application.objects.get(slug="oidc-conformance-1"),
            push_verify_certificates=False,
        )

    @retry()
    def test_openid_ssf_transmitter_test_plan(self):
        iss = self.url(
            "authentik_providers_ssf:configuration",
            application_slug="oidc-conformance-1",
        )
        self.run_test(
            "openid-ssf-transmitter-test-plan",
            {
                "alias": "authentik",
                "description": "authentik",
                "ssf": {
                    "transmitter": {
                        "issuer": iss,
                        "configuration_metadata_endpoint": iss,
                        "access_token": self.provider.token.key,
                    }
                },
            },
            test_variant={
                "client_auth_type": "client_secret_post",
                "ssf_server_metadata": "static",
                "server_metadata": "static",
                "ssf_auth_mode": "static",
                "ssf_delivery_mode": "push",
                "ssf_profile": "caep_interop",
                "client_registration": "static_client",
            },
        )
