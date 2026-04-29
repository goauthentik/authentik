from unittest.mock import patch

import urllib3

from authentik.flows.models import Flow
from authentik.lib.utils.http import get_http_session as real_get_http_session
from authentik.providers.oauth2.models import OAuth2LogoutMethod, OAuth2Provider
from tests.decorators import retry
from tests.openid_conformance.base import TestOpenIDConformance


def _insecure_http_session():
    session = real_get_http_session()
    session.verify = False
    return session


class TestOpenIDConformanceBackchannel(TestOpenIDConformance):

    def setUp(self):
        super().setUp()
        OAuth2Provider.objects.filter(name__startswith="oidc-conformance-").update(
            invalidation_flow=Flow.objects.get(slug="default-invalidation-flow"),
            logout_method=OAuth2LogoutMethod.BACKCHANNEL,
            logout_uri="https://host.docker.internal:8443/test/a/authentik/backchannel_logout",
        )
        # Conformance suite ships a self-signed cert with no SAN; modern Python
        # SSL won't trust it under any hostname. Skip verification for this
        # test only — production keeps verify=True via get_http_session().
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self._http_patcher = patch(
            "authentik.providers.oauth2.tasks.get_http_session",
            _insecure_http_session,
        )
        self._http_patcher.start()
        self.addCleanup(self._http_patcher.stop)

    @retry()
    def test_oidcc_backchannel_logout_certification_test_plan(self):
        test_plan_name = "oidcc-backchannel-rp-initiated-logout-certification-test-plan"
        self.test_variant = {
            "client_registration": "static_client",
            "response_type": "code",
        }
        self.run_test(test_plan_name, self.test_plan_config)
