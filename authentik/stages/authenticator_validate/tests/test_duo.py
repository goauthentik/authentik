"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.planner import FlowPlan
from authentik.flows.stage import StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.tests.utils import dummy_get_response
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.challenge import validate_challenge_duo
from authentik.tenants.utils import get_tenant_for_request


class AuthenticatorValidateStageDuoTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_device_challenge_duo(self):
        """Test duo"""
        request = self.request_factory.get("/")

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        setattr(request, "tenant", get_tenant_for_request(request))

        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_key(),
            api_hostname="",
        )
        duo_device = DuoDevice.objects.create(
            user=self.user,
            stage=stage,
        )
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            MagicMock(
                auth=MagicMock(
                    return_value={
                        "result": "allow",
                        "status": "allow",
                        "status_msg": "Success. Logging you in...",
                    }
                )
            ),
        ):
            self.assertEqual(
                duo_device,
                validate_challenge_duo(
                    duo_device.pk,
                    StageView(
                        FlowExecutorView(
                            current_stage=stage,
                            plan=FlowPlan(generate_id(), [], {}),
                        ),
                        request=request,
                    ),
                    self.user,
                ),
            )
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            MagicMock(auth=MagicMock(return_value={"result": "deny"})),
        ):
            with self.assertRaises(ValidationError):
                validate_challenge_duo(
                    duo_device.pk,
                    StageView(
                        FlowExecutorView(
                            current_stage=stage,
                            plan=FlowPlan(generate_id(), [], {}),
                        ),
                        request=request,
                    ),
                    self.user,
                )
