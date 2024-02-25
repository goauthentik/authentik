"""Source stage tests"""

from django.urls import reverse

from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.enterprise.stages.source.models import SourceStage
from authentik.flows.models import FlowDesignation, FlowStageBinding, FlowToken
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.sources.saml.models import SAMLSource
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage


class TestSourceStage(FlowTestCase):
    """Source stage tests"""

    def setUp(self):
        self.source = SAMLSource.objects.create(
            slug=generate_id(),
            issuer="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def test_source_success(self):
        """Test"""
        user = create_test_user()
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = SourceStage.objects.create(name=generate_id(), source=self.source)
        FlowStageBinding.objects.create(
            target=flow,
            stage=IdentificationStage.objects.create(
                name=generate_id(),
                user_fields=[UserFields.USERNAME],
            ),
            order=0,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=PasswordStage.objects.create(name=generate_id(), backends=[BACKEND_INBUILT]),
            order=5,
        )
        FlowStageBinding.objects.create(target=flow, stage=stage, order=10)
        FlowStageBinding.objects.create(
            target=flow,
            stage=UserLoginStage.objects.create(
                name=generate_id(),
            ),
            order=15,
        )

        # Get user identification stage
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, flow, component="ak-stage-identification")
        # Send username
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={"uid_field": user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, flow, component="ak-stage-password")
        # Send password
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={"password": user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(
            response,
            reverse("authentik_sources_saml:login", kwargs={"source_slug": self.source.slug}),
        )

        # Hijack flow plan so we don't have to emulate the source
        flow_token = FlowToken.objects.filter(
            identifier__startswith=f"ak-source-stage-{stage.name.lower()}"
        ).first()
        self.assertIsNotNone(flow_token)
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        plan.context[PLAN_CONTEXT_IS_RESTORED] = flow_token
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # Pretend we've just returned from the source
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
