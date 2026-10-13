"""SAML Source flow manager tests for re-authentication"""

from base64 import b64encode
from unittest.mock import patch

from django.test import TestCase
from freezegun import freeze_time

from authentik.core.sources.stage import PostSourceStage
from authentik.core.tests.utils import RequestFactory, create_test_flow, create_test_user
from authentik.flows.models import FlowAuthenticationRequirement, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.policies.denied import AccessDeniedResponse
from authentik.sources.saml.models import SAMLSource, UserSAMLSourceConnection
from authentik.sources.saml.processors.response import ResponseProcessor

GOOGLE_ACS_URL = "https://127.0.0.1:9443/source/saml/google/acs/"


class TestSAMLSourceFlowManagerReauth(TestCase):
    """Re-authenticating an already-logged-in user through a SAML source whose
    authentication flow requires an unauthenticated request.

    ForceAuthn re-authenticates a logged-in session by redirecting it into the
    authentication flow, which may forward the user to an upstream source; when the
    source callback runs, the request is still authenticated, so the source must be
    able to run its authentication flow for the same user
    (https://github.com/goauthentik/authentik/issues/26861).
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override="https://accounts.google.com/o/saml2?idpid=",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
            authentication_flow=create_test_flow(
                FlowDesignation.AUTHENTICATION,
                authentication=FlowAuthenticationRequirement.REQUIRE_UNAUTHENTICATED,
            ),
        )

    @freeze_time("2022-10-14T14:15:00")
    def _flow_manager_for(self, request):
        """Parse the fixture SAML response and return its flow manager"""
        with patch(
            "authentik.sources.saml.processors.response.reverse",
            return_value=GOOGLE_ACS_URL,
        ):
            parser = ResponseProcessor(self.source, request)
            parser.parse()
            return parser.prepare_flow_manager()

    def _post_response(self, user):
        """POST request carrying the fixture SAML response"""
        return self.factory.post(
            "/",
            user=user,
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )

    @freeze_time("2022-10-14T14:15:00")
    def test_reauth_same_user_allowed(self):
        """An authenticated session re-authenticating as the same user may run the
        source authentication flow even though it requires an unauthenticated
        request: the planner exempts the session user when the flow is planned with
        them as pending user"""
        user = create_test_user()
        UserSAMLSourceConnection.objects.create(
            user=user, source=self.source, identifier="jens@goauthentik.io"
        )

        request = self._post_response(user)
        flow_manager = self._flow_manager_for(request)
        response = flow_manager.get_flow()

        self.assertEqual(response.status_code, 302)
        plan = request.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.bindings[0].stage.view, PostSourceStage)
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], user)

    @freeze_time("2022-10-14T14:15:00")
    def test_reauth_other_user_refused(self):
        """A session user who does not own the source connection is still refused"""
        UserSAMLSourceConnection.objects.create(
            user=create_test_user(), source=self.source, identifier="jens@goauthentik.io"
        )

        request = self._post_response(create_test_user())
        flow_manager = self._flow_manager_for(request)
        response = flow_manager.get_flow()

        self.assertIsInstance(response, AccessDeniedResponse)
