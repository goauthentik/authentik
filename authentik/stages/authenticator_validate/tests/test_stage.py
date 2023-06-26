"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.test.client import RequestFactory
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding, NotConfiguredAction
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id, generate_key
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageSerializer
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_validate.stage import PLAN_CONTEXT_DEVICE_CHALLENGES
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_not_configured_action(self):
        """Test not_configured_action"""
        conf_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            not_configured_action=NotConfiguredAction.CONFIGURE,
        )
        stage.configuration_stages.set([conf_stage])
        flow = create_test_flow()
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Continue",
            user_fields=["username"],
            sources=[],
            show_source_labels=False,
        )

    def test_not_configured_action_multiple(self):
        """Test not_configured_action"""
        conf_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        conf_stage2 = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            not_configured_action=NotConfiguredAction.CONFIGURE,
        )
        stage.configuration_stages.set([conf_stage, conf_stage2])
        flow = create_test_flow()
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        # Get initial identification stage
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        # Answer initial identification stage
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        # Get list of all configuration stages
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        # Select stage
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"selected_stage": conf_stage.pk},
        )
        self.assertEqual(response.status_code, 302)
        # get actual identification stage response
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Continue",
            user_fields=["username"],
            sources=[],
            show_source_labels=False,
        )

    def test_stage_validation(self):
        """Test serializer validation"""
        self.client.force_login(self.user)
        serializer = AuthenticatorValidateStageSerializer(
            data={
                "name": generate_id(),
                "not_configured_action": NotConfiguredAction.CONFIGURE,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("not_configured_action", serializer.errors)
        serializer = AuthenticatorValidateStageSerializer(
            data={"name": generate_id(), "not_configured_action": NotConfiguredAction.DENY}
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_selected_challenge(self):
        """Test validate_selected_challenge"""
        flow = create_test_flow()
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.STATIC, DeviceClasses.TOTP],
        )

        session = self.client.session
        plan = FlowPlan(flow_pk=flow.pk.hex)
        plan.append_stage(stage)
        plan.context[PLAN_CONTEXT_DEVICE_CHALLENGES] = [
            {
                "device_class": "static",
                "device_uid": "1",
            },
            {
                "device_class": "totp",
                "device_uid": "2",
            },
        ]
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={
                "selected_challenge": {
                    "device_class": "baz",
                    "device_uid": "quox",
                    "challenge": {},
                }
            },
        )
        self.assertStageResponse(
            response,
            flow,
            response_errors={
                "selected_challenge": [{"string": "invalid challenge selected", "code": "invalid"}]
            },
            component="ak-stage-authenticator-validate",
        )

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={
                "selected_challenge": {
                    "device_class": "static",
                    "device_uid": "1",
                    "challenge": {},
                },
            },
        )
        self.assertStageResponse(
            response,
            flow,
            response_errors={"non_field_errors": [{"string": "Empty response", "code": "invalid"}]},
            component="ak-stage-authenticator-validate",
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
    def test_non_authentication_flow(self):
        """Test full in an authorization flow (no pending user)"""
        self.client.force_login(self.user)
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

        flow = create_test_flow(FlowDesignation.AUTHORIZATION)
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.DUO],
        )

        plan = FlowPlan(flow_pk=flow.pk.hex)
        plan.append(FlowStageBinding.objects.create(target=flow, stage=stage, order=2))
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
