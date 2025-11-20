from unittest.mock import PropertyMock, patch

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.constants import PASSWORD_HASH_UPGRADE_REASON
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage


class TestAudit(APITestCase):
    """Test audit middleware"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        # Set up a flow for authentication
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = IdentificationStage.objects.create(
            name="identification",
            user_fields=[UserFields.USERNAME],
            pretend_user_exists=False,
        )
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_INBUILT])
        self.stage.password_stage = pw_stage
        self.stage.save()
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def test_password_hash_updated(self):
        """
        When Django is updated, it's possible that the password hash is also updated.

        Due to an increase in the password hash rounds.
        When this happens, we should log a MODEL_UPDATED event with a reason
        explaining the password hash upgrade.
        """
        with patch.object(
            PBKDF2PasswordHasher,
            "iterations",
            new_callable=PropertyMock,
            return_value=PBKDF2PasswordHasher.iterations + 100_000,
        ):
            # During authentication,
            # Django should detect that the hash needs to be updated and update it
            form_data = {"uid_field": self.user.username, "password": self.user.username}
            url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            response = self.client.post(url, form_data)
            self.assertEqual(response.status_code, 200)

        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__app="authentik_core",
            context__model__model_name="user",
            context__model__pk=self.user.pk,
            context__reason=PASSWORD_HASH_UPGRADE_REASON,
        )
        self.assertTrue(events.exists())

    def test_set_password_no_password_upgrade_reason(self):
        """Ensure that setting a password is not detected as a password hash upgrade."""
        self.client.login(username=self.user.username, password=self.user.username)
        response = self.client.post(
            reverse("authentik_api:user-set-password", kwargs={"pk": self.user.pk}),
            data={"password": generate_id()},
        )
        self.assertEqual(response.status_code, 204)

        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__app="authentik_core",
            context__model__model_name="user",
            context__model__pk=self.user.pk,
            context__reason=PASSWORD_HASH_UPGRADE_REASON,
        )
        self.assertFalse(events.exists())
