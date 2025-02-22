"""Test validator stage"""

from unittest.mock import MagicMock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from authentik.brands.utils import get_brand_for_request
from authentik.core.middleware import RESPONSE_HEADER_ID
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN, FlowExecutorView
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.tests.utils import dummy_get_response
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.challenge import validate_challenge_duo
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.user_login.models import UserLoginStage


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
        request.brand = get_brand_for_request(request)

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
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.auth_client",
            MagicMock(
                return_value=MagicMock(
                    auth=MagicMock(
                        return_value={
                            "result": "allow",
                            "status": "allow",
                            "status_msg": "Success. Logging you in...",
                        }
                    )
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
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.auth_client",
            MagicMock(
                return_value=MagicMock(
                    auth=MagicMock(
                        return_value={
                            "result": "deny",
                            "status": "deny",
                            "status_msg": "foo",
                        }
                    )
                )
            ),
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

    @patch(
        "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.auth_client",
        MagicMock(
            return_value=MagicMock(
                auth=MagicMock(
                    return_value={
                        "result": "allow",
                        "status": "allow",
                        "status_msg": "Success. Logging you in...",
                    }
                )
            )
        ),
    )
    def test_full(self):
        """Test full within a flow executor"""
        duo_stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_key(),
            api_hostname="",
        )
        duo_device = DuoDevice.objects.create(
            user=self.user,
            stage=duo_stage,
        )

        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.DUO],
        )

        plan = FlowPlan(flow_pk=flow.pk.hex)
        plan.append(FlowStageBinding.objects.create(target=flow, stage=stage, order=2))
        plan.append(
            FlowStageBinding.objects.create(
                target=flow, stage=UserLoginStage.objects.create(name=generate_id()), order=3
            )
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"duo": duo_device.pk},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            user__pk=self.user.pk,
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(
            event.context,
            {
                "auth_method": "auth_mfa",
                "auth_method_args": {
                    "mfa_devices": [
                        {
                            "app": "authentik_stages_authenticator_duo",
                            "model_name": "duodevice",
                            "name": "",
                            "pk": duo_device.pk,
                        }
                    ]
                },
                "http_request": {
                    "args": {},
                    "method": "GET",
                    "path": f"/api/v3/flows/executor/{flow.slug}/",
                    "user_agent": "",
                    "request_id": response[RESPONSE_HEADER_ID],
                },
            },
        )
