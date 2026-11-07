"""Stage duplication API tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.endpoints.models import StageMode
from authentik.enterprise.stages.mtls.models import CertAttributes, MutualTLSStage, UserAttributes
from authentik.enterprise.tests import enterprise_test
from authentik.flows.models import FlowStageBinding, Stage
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.rbac.models import Role
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSProviders
from authentik.stages.email.models import EmailStage
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_write.models import UserWriteStage


class TestStageDuplicateAPI(APITestCase):
    """Stage duplication API tests"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)

    def duplicate(self, stage: Stage, name: str):
        return self.client.post(
            reverse("authentik_api:stage-duplicate", kwargs={"pk": stage.pk}),
            data={"name": name},
        )

    def test_prompt_stage(self):
        """A copy refers to the same prompts and policies, and leaves the original's bindings"""
        prompt = Prompt.objects.create(
            name=generate_id(), field_key=generate_id(), label=generate_id(), type=FieldTypes.TEXT
        )
        policy = ExpressionPolicy.objects.create(name=generate_id(), expression="return True")
        stage = PromptStage.objects.create(name=generate_id())
        stage.fields.set([prompt])
        stage.validation_policies.set([policy])
        FlowStageBinding.objects.create(target=create_test_flow(), stage=stage, order=0)
        name = generate_id()

        response = self.duplicate(stage, name)

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["name"], name)
        self.assertEqual(body["component"], "ak-stage-prompt-form")
        self.assertEqual(body["flow_set"], [])
        copy = PromptStage.objects.get(pk=body["pk"])
        self.assertNotEqual(copy.pk, stage.pk)
        self.assertEqual(list(copy.fields.all()), [prompt])
        self.assertEqual(list(copy.validation_policies.all()), [policy])
        self.assertFalse(FlowStageBinding.objects.filter(stage=copy).exists())
        self.assertEqual(FlowStageBinding.objects.filter(stage=stage).count(), 1)
        self.assertEqual(Prompt.objects.filter(field_key=prompt.field_key).count(), 1)

    def test_identification_stage(self):
        """A copy keeps the original's settings, foreign keys and sources"""
        source = OAuthSource.objects.create(name=generate_id(), slug=generate_id())
        password_stage = PasswordStage.objects.create(name=generate_id(), backends=[])
        enrollment_flow = create_test_flow()
        stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.E_MAIL, UserFields.USERNAME],
            password_stage=password_stage,
            enrollment_flow=enrollment_flow,
            case_insensitive_matching=False,
            show_source_labels=True,
        )
        stage.sources.set([source])

        response = self.duplicate(stage, generate_id())

        self.assertEqual(response.status_code, 201)
        copy = IdentificationStage.objects.get(pk=response.json()["pk"])
        self.assertEqual(copy.user_fields, [UserFields.E_MAIL, UserFields.USERNAME])
        self.assertEqual(copy.password_stage, password_stage)
        self.assertEqual(copy.enrollment_flow, enrollment_flow)
        self.assertFalse(copy.case_insensitive_matching)
        self.assertTrue(copy.show_source_labels)
        self.assertEqual(list(copy.sources.values_list("pk", flat=True)), [source.pk])

    def test_user_write_stage(self):
        """A copy keeps a foreign key with a default"""
        group = Group.objects.create(name=generate_id())
        stage = UserWriteStage.objects.create(name=generate_id(), create_users_group=group)

        response = self.duplicate(stage, generate_id())

        self.assertEqual(response.status_code, 201)
        copy = UserWriteStage.objects.get(pk=response.json()["pk"])
        self.assertEqual(copy.create_users_group, group)

    def test_name_taken(self):
        """The copy's name must be unique among all stages"""
        other = UserWriteStage.objects.create(name=generate_id())
        stage = PromptStage.objects.create(name=generate_id())
        count = Stage.objects.count()

        response = self.duplicate(stage, other.name)

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertEqual(Stage.objects.count(), count)

    def test_enterprise_stage_unlicensed(self):
        """Duplicating needs a license where creating the stage type does"""
        stage = MutualTLSStage.objects.create(
            name=generate_id(),
            mode=StageMode.REQUIRED,
            cert_attribute=CertAttributes.COMMON_NAME,
            user_attribute=UserAttributes.USERNAME,
        )

        response = self.duplicate(stage, generate_id())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(MutualTLSStage.objects.count(), 1)

    @enterprise_test()
    def test_enterprise_stage(self):
        """A licensed copy of an enterprise stage keeps its certificate authorities"""
        ca = create_test_cert()
        stage = MutualTLSStage.objects.create(
            name=generate_id(),
            mode=StageMode.REQUIRED,
            cert_attribute=CertAttributes.COMMON_NAME,
            user_attribute=UserAttributes.USERNAME,
        )
        stage.certificate_authorities.set([ca])

        response = self.duplicate(stage, generate_id())

        self.assertEqual(response.status_code, 201)
        copy = MutualTLSStage.objects.get(pk=response.json()["pk"])
        self.assertEqual(list(copy.certificate_authorities.all()), [ca])


class TestStageDuplicatePermissions(APITestCase):
    """Duplicating a stage needs to see it in the all-stages endpoint, view on it and add for its
    type"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.client.force_login(self.user)
        self.password = generate_id()
        self.stage = EmailStage.objects.create(name=generate_id(), password=self.password)

    def duplicate(self, stage: Stage | None = None):
        return self.client.post(
            reverse("authentik_api:stage-duplicate", kwargs={"pk": (stage or self.stage).pk}),
            data={"name": generate_id()},
        )

    def assign_type_perms(self, *verbs: str):
        self.role.assign_perms("authentik_flows.view_stage")
        self.role.assign_perms(
            [f"authentik_stages_email.{verb}_emailstage" for verb in verbs], self.stage
        )
        self.role.assign_perms("authentik_stages_email.add_emailstage")

    def test_no_permissions(self):
        """Without any permission the stage isn't duplicated"""
        self.assertEqual(self.duplicate().status_code, 403)
        self.assertEqual(EmailStage.objects.count(), 1)

    def test_view_without_add(self):
        """Viewing a stage alone doesn't allow creating another"""
        self.role.assign_perms("authentik_flows.view_stage")
        self.role.assign_perms("authentik_stages_email.view_emailstage", self.stage)
        self.assertEqual(self.duplicate().status_code, 403)
        self.assertEqual(EmailStage.objects.count(), 1)

    def test_add_without_view(self):
        """Adding stages of a type doesn't allow copying one the user can't view"""
        self.role.assign_perms(
            ["authentik_flows.view_stage", "authentik_stages_email.add_emailstage"]
        )
        self.assertEqual(self.duplicate().status_code, 403)
        self.assertEqual(EmailStage.objects.count(), 1)

    def test_base_stage_permissions(self):
        """Permissions on the base stage model say nothing about the stage's type"""
        self.role.assign_perms(["authentik_flows.view_stage", "authentik_flows.add_stage"])
        self.assertEqual(self.duplicate().status_code, 403)
        self.assertEqual(EmailStage.objects.count(), 1)

    def test_hidden_from_all_stages(self):
        """A stage the all-stages endpoint doesn't show can't be duplicated through it"""
        self.role.assign_perms("authentik_stages_email.view_emailstage", self.stage)
        self.role.assign_perms("authentik_stages_email.add_emailstage")
        self.assertEqual(self.duplicate().status_code, 403)
        self.assertEqual(EmailStage.objects.count(), 1)

    def test_view_and_add_without_secrets(self):
        """A user who can't change the original gets a copy without its secrets"""
        self.assign_type_perms("view")

        response = self.duplicate()

        self.assertEqual(response.status_code, 201)
        copy = EmailStage.objects.get(pk=response.json()["pk"])
        self.assertEqual(copy.host, self.stage.host)
        self.assertEqual(copy.password, "")

    def test_change_and_add_with_secrets(self):
        """A user who can change the original gets a copy with its secrets"""
        self.assign_type_perms("view", "change")

        response = self.duplicate()

        self.assertEqual(response.status_code, 201)
        copy = EmailStage.objects.get(pk=response.json()["pk"])
        self.assertEqual(copy.password, self.password)

    def test_required_secret_without_change(self):
        """A stage type that requires a secret can't be copied without it"""
        stage = AuthenticatorSMSStage.objects.create(
            name=generate_id(),
            provider=SMSProviders.GENERIC,
            from_number=generate_id(),
            account_sid=generate_id(),
            auth=generate_id(),
        )
        self.role.assign_perms("authentik_flows.view_stage")
        self.role.assign_perms(
            "authentik_stages_authenticator_sms.view_authenticatorsmsstage", stage
        )
        self.role.assign_perms("authentik_stages_authenticator_sms.add_authenticatorsmsstage")
        count = AuthenticatorSMSStage.objects.count()

        response = self.duplicate(stage)

        self.assertEqual(response.status_code, 403)
        self.assertIn("permission to change it", response.json()["detail"])
        self.assertEqual(AuthenticatorSMSStage.objects.count(), count)
