"""Test duo stage"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test.client import RequestFactory
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_duo.stage import SESSION_KEY_DUO_ENROLL
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorDuoStageTests(FlowTestCase):
    """Test duo stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_client(self):
        """Test Duo client setup"""
        stage = AuthenticatorDuoStage(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            admin_integration_key=generate_id(),
            admin_secret_key=generate_id(),
            api_hostname=generate_id(),
        )
        self.assertEqual(stage.auth_client().ikey, stage.client_id)
        self.assertEqual(stage.admin_client().ikey, stage.admin_integration_key)
        stage.admin_integration_key = ""
        with self.assertRaises(ValueError):
            self.assertEqual(stage.admin_client().ikey, stage.admin_integration_key)

    def test_api_enrollment_invalid(self):
        """Test `enrollment_status`"""
        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-enrollment-status",
                kwargs={
                    "pk": str(uuid4()),
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_api_enrollment(self):
        """Test `enrollment_status`"""
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )

        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-enrollment-status",
                kwargs={
                    "pk": str(stage.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 400)

        session = self.client.session
        session[SESSION_KEY_DUO_ENROLL] = {"user_id": "foo", "activation_code": "bar"}
        session.save()

        with patch("duo_client.auth.Auth.enroll_status", MagicMock(return_value="foo")):
            response = self.client.post(
                reverse(
                    "authentik_api:authenticatorduostage-enrollment-status",
                    kwargs={
                        "pk": str(stage.pk),
                    },
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), '{"duo_response":"foo"}')

    def test_api_import_manual_invalid_username(self):
        """Test `import_device_manual`"""
        self.client.force_login(self.user)
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )
        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-import-device-manual",
                kwargs={
                    "pk": str(stage.pk),
                },
            ),
            data={
                "username": generate_id(),
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_api_import_manual_duplicate_device(self):
        """Test `import_device_manual`"""
        self.client.force_login(self.user)
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )
        device = DuoDevice.objects.create(
            name="foo",
            duo_user_id=generate_id(),
            user=self.user,
            stage=stage,
        )
        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-import-device-manual",
                kwargs={
                    "pk": str(stage.pk),
                },
            ),
            data={
                "username": self.user.username,
                "duo_user_id": device.duo_user_id,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_api_import_manual(self):
        """Test `import_device_manual`"""
        self.client.force_login(self.user)
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )
        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-import-device-manual",
                kwargs={
                    "pk": str(stage.pk),
                },
            ),
            data={
                "username": self.user.username,
                "duo_user_id": "foo",
            },
        )
        self.assertEqual(response.status_code, 204)

    def test_api_import_automatic_invalid(self):
        """test `import_devices_automatic`"""
        self.client.force_login(self.user)
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )
        response = self.client.post(
            reverse(
                "authentik_api:authenticatorduostage-import-devices-automatic",
                kwargs={
                    "pk": str(stage.pk),
                },
            ),
        )
        self.assertEqual(response.status_code, 400)

    def test_api_import_automatic(self):
        """test `import_devices_automatic`"""
        self.client.force_login(self.user)
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            admin_integration_key=generate_id(),
            admin_secret_key=generate_id(),
            api_hostname=generate_id(),
        )
        device = DuoDevice.objects.create(
            name="foo",
            duo_user_id=generate_id(),
            user=self.user,
            stage=stage,
        )
        with patch(
            "duo_client.admin.Admin.get_users_iterator",
            MagicMock(
                return_value=[
                    {
                        "user_id": "foo",
                        "username": "bar",
                    },
                    {
                        "user_id": device.duo_user_id,
                        "username": self.user.username,
                    },
                    {
                        "user_id": generate_id(),
                        "username": self.user.username,
                    },
                ]
            ),
        ):
            response = self.client.post(
                reverse(
                    "authentik_api:authenticatorduostage-import-devices-automatic",
                    kwargs={
                        "pk": str(stage.pk),
                    },
                ),
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), '{"error":"","count":1}')

    def test_stage_enroll_basic(self):
        """Test stage"""
        conf_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        stage = AuthenticatorDuoStage.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            api_hostname=generate_id(),
        )
        flow = create_test_flow()
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)

        enroll_mock = MagicMock(
            return_value={
                "user_id": "foo",
                "activation_barcode": "bar",
                "activation_code": "bar",
            }
        )
        with patch("duo_client.auth.Auth.enroll", enroll_mock):
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                follow=True,
            )
            self.assertStageResponse(
                response,
                flow,
                component="ak-stage-authenticator-duo",
                pending_user=self.user.username,
                activation_barcode="bar",
                activation_code="bar",
            )

            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                follow=True,
            )
            self.assertStageResponse(
                response,
                flow,
                component="ak-stage-authenticator-duo",
                pending_user=self.user.username,
                activation_barcode="bar",
                activation_code="bar",
            )
            self.assertEqual(enroll_mock.call_count, 1)

            with patch("duo_client.auth.Auth.enroll_status", MagicMock(return_value="success")):
                response = self.client.post(
                    reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}), {}
                )
                self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
