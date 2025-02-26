"""read only tests"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils.timezone import now

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import (
    THRESHOLD_READ_ONLY_WEEKS,
    License,
    LicenseUsage,
    LicenseUsageStatus,
)
from authentik.enterprise.tests.test_license import expiry_valid
from authentik.flows.models import (
    FlowDesignation,
    FlowStageBinding,
)
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage


class TestReadOnly(FlowTestCase):
    """Test read_only"""

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_login(self):
        """Test flow, ensure login is still possible with read only mode"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)
        usage.save(update_fields=["record_date"])

        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )

        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.E_MAIL],
            pretend_user_exists=False,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=ident_stage,
            order=0,
        )
        password_stage = PasswordStage.objects.create(
            name=generate_id(), backends=[BACKEND_INBUILT]
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=password_stage,
            order=1,
        )
        login_stage = UserLoginStage.objects.create(
            name=generate_id(),
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=login_stage,
            order=2,
        )

        user = create_test_user()

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            sources=[],
            show_source_labels=False,
            user_fields=[UserFields.E_MAIL],
        )
        response = self.client.post(exec_url, {"uid_field": user.email}, follow=True)
        self.assertStageResponse(response, flow, component="ak-stage-password")
        response = self.client.post(exec_url, {"password": user.username}, follow=True)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_manage_licenses(self):
        """Test that managing licenses is still possible"""
        license = License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)
        usage.save(update_fields=["record_date"])

        admin = create_test_admin_user()
        self.client.force_login(admin)

        # Reading is always allowed
        response = self.client.get(reverse("authentik_api:license-list"))
        self.assertEqual(response.status_code, 200)

        # Writing should also be allowed
        response = self.client.patch(
            reverse("authentik_api:license-detail", kwargs={"pk": license.pk})
        )
        self.assertEqual(response.status_code, 200)

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_manage_flows(self):
        """Test flow"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)
        usage.save(update_fields=["record_date"])

        admin = create_test_admin_user()
        self.client.force_login(admin)

        # Read only is still allowed
        response = self.client.get(reverse("authentik_api:flow-list"))
        self.assertEqual(response.status_code, 200)

        flow = create_test_flow()
        # Writing is not
        response = self.client.patch(
            reverse("authentik_api:flow-detail", kwargs={"slug": flow.slug})
        )
        self.assertJSONEqual(
            response.content,
            {"detail": "Request denied due to expired/invalid license.", "code": "denied_license"},
        )
        self.assertEqual(response.status_code, 400)

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_manage_users(self):
        """Test that managing users is still possible"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)
        usage.save(update_fields=["record_date"])

        admin = create_test_admin_user()
        self.client.force_login(admin)

        # Reading is always allowed
        response = self.client.get(reverse("authentik_api:user-list"))
        self.assertEqual(response.status_code, 200)

        # Writing should also be allowed
        response = self.client.patch(reverse("authentik_api:user-detail", kwargs={"pk": admin.pk}))
        self.assertEqual(response.status_code, 200)
