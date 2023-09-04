"""Test validator stage"""
from datetime import datetime, timedelta
from hashlib import sha256
from time import sleep

from django.test.client import RequestFactory
from django.urls.base import reverse
from jwt import encode
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding, NotConfiguredAction
from authentik.flows.stage import StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.root.install_id import get_install_id
from authentik.stages.authenticator.oath import TOTP
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_validate.challenge import (
    get_challenge_for_device,
    validate_challenge_code,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_validate.stage import COOKIE_NAME_MFA
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageTOTPTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)

    def test_last_auth_threshold(self):
        """Test last_auth_threshold"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        # Verify token once here to set last_t etc
        totp = TOTP(device.bin_key)
        sleep(1)
        self.assertTrue(device.verify_token(totp.token()))
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="milliseconds=0",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            follow=True,
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-authenticator-validate",
        )

    def test_last_auth_threshold_valid(self):
        """Test last_auth_threshold"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        # Verify token once here to set last_t etc
        totp = TOTP(device.bin_key)
        sleep(1)
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"code": str(totp.token())},
        )
        self.assertIn(COOKIE_NAME_MFA, response.cookies)
        self.assertStageResponse(response, component="xak-flow-redirect", to="/")

    def test_last_auth_skip(self):
        """Test valid cookie"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        # Verify token once here to set last_t etc
        totp = TOTP(device.bin_key)
        sleep(1)
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"code": str(totp.token())},
        )
        self.assertIn(COOKIE_NAME_MFA, response.cookies)
        self.assertStageResponse(response, component="xak-flow-redirect", to="/")
        mfa_cookie = response.cookies[COOKIE_NAME_MFA]
        self.client.logout()
        self.client.cookies[COOKIE_NAME_MFA] = mfa_cookie
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(response, component="xak-flow-redirect", to="/")

    def test_last_auth_stage_pk(self):
        """Test MFA cookie with wrong stage PK"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)
        self.client.cookies[COOKIE_NAME_MFA] = encode(
            payload={
                "device": device.pk,
                "stage": stage.pk.hex + generate_id(),
                "exp": (datetime.now() + timedelta(days=3)).timestamp(),
            },
            key=sha256(f"{get_install_id()}:{stage.pk.hex}".encode("ascii")).hexdigest(),
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(response, component="ak-stage-authenticator-validate")

    def test_last_auth_stage_device(self):
        """Test MFA cookie with wrong device PK"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)
        self.client.cookies[COOKIE_NAME_MFA] = encode(
            payload={
                "device": device.pk + 1,
                "stage": stage.pk.hex,
                "exp": (datetime.now() + timedelta(days=3)).timestamp(),
            },
            key=sha256(f"{get_install_id()}:{stage.pk.hex}".encode("ascii")).hexdigest(),
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(response, component="ak-stage-authenticator-validate")

    def test_last_auth_stage_expired(self):
        """Test MFA cookie with expired cookie"""
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        stage.configuration_stages.set([ident_stage])
        FlowStageBinding.objects.create(target=self.flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=1)
        self.client.cookies[COOKIE_NAME_MFA] = encode(
            payload={
                "device": device.pk,
                "stage": stage.pk.hex,
                "exp": (datetime.now() - timedelta(days=3)).timestamp(),
            },
            key=sha256(f"{get_install_id()}:{stage.pk.hex}".encode("ascii")).hexdigest(),
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(response, component="ak-stage-authenticator-validate")

    def test_device_challenge_totp(self):
        """Test device challenge"""
        request = self.request_factory.get("/")
        totp_device = TOTPDevice.objects.create(user=self.user, confirmed=True, digits=6)
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
        )
        self.assertEqual(get_challenge_for_device(request, stage, totp_device), {})
        with self.assertRaises(ValidationError):
            validate_challenge_code(
                "1234", StageView(FlowExecutorView(current_stage=stage), request=request), self.user
            )
