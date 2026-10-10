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


@patch("authentik.providers.oauth2.tasks.get_http_session", _insecure_http_session)
class TestOpenIDConformanceBackchannel(TestOpenIDConformance):
    def setUp(self):
        super().setUp()
        OAuth2Provider.objects.filter(name__startswith="oidc-conformance-").update(
            invalidation_flow=Flow.objects.get(slug="default-invalidation-flow"),
            logout_method=OAuth2LogoutMethod.BACKCHANNEL,
            logout_uri="https://localhost:8443/test/a/authentik/backchannel_logout",
        )
        # We are unable to use https for this at the current time
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @retry()
    def test_oidcc_backchannel_logout_certification_test_plan(self):
        self.run_test(
            "oidcc-backchannel-rp-initiated-logout-certification-test-plan",
            self.test_plan_config,
            {
                "client_registration": "static_client",
                "response_type": "code",
            },
        )
