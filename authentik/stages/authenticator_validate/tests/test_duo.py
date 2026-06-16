"""Test validator stage"""

from unittest.mock import MagicMock, patch

from django.urls import reverse

from authentik.brands.utils import get_brand_for_request
from authentik.core.middleware import RESPONSE_HEADER_ID
from authentik.core.models import Application
from authentik.core.tests.utils import RequestFactory, create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id, generate_key
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.challenge import ChallengeValidationError, FlowContext
from authentik.stages.authenticator_validate.challenge.duo import DuoChallenger
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

        request.brand = get_brand_for_request(request)

        application = Application()

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
        challenger = DuoChallenger(request, stage, FlowContext(application=application))
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
                challenger.validate(DuoDevice.objects.filter(pk=duo_device.pk), {}, duo_device.pk),
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
            challenger = DuoChallenger(request, stage, FlowContext(application=application))
            with self.assertRaises(ChallengeValidationError):
                challenger.validate(DuoDevice.objects.filter(pk=duo_device.pk), {}, duo_device.pk)

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

        challenge_uid = response.json()["device_challenges"][0]["uid"]

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"duo": duo_device.pk, "challenge_uid": challenge_uid},
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
                    "known_device": False,
                    "mfa_devices": [
                        {
                            "app": "authentik_stages_authenticator_duo",
                            "model_name": "duodevice",
                            "name": "",
                            "pk": duo_device.pk,
                        }
                    ],
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
