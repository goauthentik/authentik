"""Source stage tests"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import SourceUserMatchingModes
from authentik.core.sources.flow_manager import (
    PLAN_CONTEXT_SOURCE_MATCH_FAILURE,
    PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG,
    SESSION_KEY_OVERRIDE_FLOW_TOKEN,
    SESSION_KEY_SOURCE_FLOW_CONTEXT,
    SESSION_KEY_SOURCE_FLOW_STAGES,
    MatchFailureConfig,
)
from authentik.core.sources.matcher import MatchFailure, MatchFailureReason
from authentik.core.tests.utils import RequestFactory, create_test_flow, create_test_user
from authentik.enterprise.stages.source.models import SourceStage
from authentik.enterprise.stages.source.stage import SourceStageFinal
from authentik.flows.models import (
    Flow,
    FlowDesignation,
    FlowStageBinding,
    FlowToken,
    in_memory_stage,
)
from authentik.flows.planner import (
    PLAN_CONTEXT_IS_REDIRECTED,
    PLAN_CONTEXT_IS_RESTORED,
    FlowPlan,
)
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.denied import AccessDeniedResponse
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.response import SAMLSourceFlowManager
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage


class TestSourceStage(FlowTestCase):
    """Source stage tests"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            slug=generate_id(),
            issuer_override="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def create_source_plan(self, source, resume_on_match_failures: list[str]):
        """Create a suspended Source Stage plan for a source."""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = SourceStage.objects.create(
            name=generate_id(),
            source=source,
            resume_on_match_failures=resume_on_match_failures,
        )
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=10)
        plan = FlowPlan(flow_pk=flow.pk.hex)
        plan.append(binding)
        if resume_on_match_failures:
            plan.context[PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG] = MatchFailureConfig(
                reasons=resume_on_match_failures,
                source_pk=str(source.pk),
                stage_pk=str(stage.pk),
            )
        token = FlowToken.objects.create(
            expires=now() + timedelta(minutes=30),
            user=get_anonymous_user(),
            identifier=generate_id(),
            flow=flow,
            _plan=FlowToken.pickle(plan),
        )
        request = self.request_factory.get("/", user=AnonymousUser())
        request.session[SESSION_KEY_OVERRIDE_FLOW_TOKEN] = token
        request.session[SESSION_KEY_SOURCE_FLOW_STAGES] = [in_memory_stage(SourceStageFinal)]
        request.session[SESSION_KEY_SOURCE_FLOW_CONTEXT] = {
            PLAN_CONTEXT_IS_REDIRECTED: flow,
        }
        request.session.save()
        return request, token

    def create_oauth_source_plan(self, resume: bool):
        """Create a suspended Source Stage plan for an OAuth source."""
        source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
            user_matching_mode=SourceUserMatchingModes.EMAIL_LINK,
        )
        reasons = [MatchFailureReason.MISSING_PROPERTY] if resume else []
        request, token = self.create_source_plan(source, reasons)
        return source, request, token

    def test_missing_match_property_resume(self):
        """Missing OIDC properties can resume an opted-in parent flow."""
        source, request, token = self.create_oauth_source_plan(resume=True)
        userinfo = {"sub": generate_id()}
        manager = OAuthSourceFlowManager(
            source,
            request,
            userinfo["sub"],
            {"info": userinfo},
            {"oauth_userinfo": userinfo},
        )

        response = manager.get_flow()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(FlowToken.objects.filter(pk=token.pk).exists())
        self.assertFalse(UserOAuthSourceConnection.objects.filter(source=source).exists())
        restored_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        self.assertEqual(restored_plan.context["oauth_userinfo"], userinfo)
        self.assertEqual(
            restored_plan.context[PLAN_CONTEXT_SOURCE_MATCH_FAILURE],
            MatchFailure(
                reason=MatchFailureReason.MISSING_PROPERTY,
                property="email",
                source_slug=source.slug,
            ),
        )
        self.assertNotIn(
            PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG,
            restored_plan.context,
        )
        request.session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = request.session.session_key
        with self.assertFlowFinishes():
            self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": token.flow.slug})
            )
        session = self.client.session
        self.assertNotIn(SESSION_KEY_OVERRIDE_FLOW_TOKEN, session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_STAGES, session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_CONTEXT, session)

    def test_missing_match_property_default_denies(self):
        """Missing OIDC properties retain the existing behavior by default."""
        source, request, token = self.create_oauth_source_plan(resume=False)
        userinfo = {"sub": generate_id()}
        manager = OAuthSourceFlowManager(
            source,
            request,
            userinfo["sub"],
            {"info": userinfo},
            {"oauth_userinfo": userinfo},
        )

        response = manager.get_flow()

        self.assertIsInstance(response, AccessDeniedResponse)
        self.assertTrue(FlowToken.objects.filter(pk=token.pk).exists())
        self.assertFalse(UserOAuthSourceConnection.objects.filter(source=source).exists())

    def test_missing_match_property_expired_token_denies(self):
        """Missing OIDC properties cannot resume an expired parent flow."""
        source, request, token = self.create_oauth_source_plan(resume=True)
        token.expires = now() - timedelta(seconds=1)
        token.save(update_fields=("expires",))
        userinfo = {"sub": generate_id()}
        manager = OAuthSourceFlowManager(
            source,
            request,
            userinfo["sub"],
            {"info": userinfo},
            {"oauth_userinfo": userinfo},
        )

        response = manager.get_flow()

        self.assertIsInstance(response, AccessDeniedResponse)
        self.assertFalse(FlowToken.objects.filter(pk=token.pk).exists())
        self.assertFalse(UserOAuthSourceConnection.objects.filter(source=source).exists())
        self.assertNotIn(SESSION_KEY_OVERRIDE_FLOW_TOKEN, request.session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_STAGES, request.session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_CONTEXT, request.session)

    def test_saml_missing_match_property_resume(self):
        """SAML sources use the generic matching failure resume behavior."""
        request, token = self.create_source_plan(self.source, [MatchFailureReason.MISSING_PROPERTY])
        manager = SAMLSourceFlowManager.__new__(SAMLSourceFlowManager)
        manager.source = self.source
        manager.request = request
        manager.policy_context = {"saml_response": b"<Response />"}

        failure = MatchFailure(
            reason=MatchFailureReason.MISSING_PROPERTY,
            property="email",
            source_slug=self.source.slug,
        )

        response = manager.handle_match_failure(failure)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(FlowToken.objects.filter(pk=token.pk).exists())
        restored_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        self.assertEqual(restored_plan.context["saml_response"], b"<Response />")
        self.assertEqual(restored_plan.context[PLAN_CONTEXT_SOURCE_MATCH_FAILURE], failure)

    def run_to_source_redirect(self) -> tuple[Flow, SourceStage, FlowToken]:
        """Run a flow with a bound Source Stage up to the point where the user is sent
        to the source, and return the token that can resume it."""
        user = create_test_user()
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = SourceStage.objects.create(
            name=generate_id(),
            source=self.source,
            resume_on_match_failures=[MatchFailureReason.MISSING_PROPERTY],
        )
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
        self.assertStageResponse(
            response,
            flow,
            component="xak-flow-redirect",
            to=reverse("authentik_sources_saml:login", kwargs={"source_slug": self.source.slug}),
            final_redirect=False,
        )

        flow_token = FlowToken.objects.filter(
            identifier__startswith=f"ak-source-stage-{stage.name.lower()}"
        ).first()
        self.assertIsNotNone(flow_token)
        return flow, stage, flow_token

    def test_source_success(self):
        """Test"""
        flow, stage, flow_token = self.run_to_source_redirect()
        self.assertEqual(
            flow_token.plan.context[PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG],
            MatchFailureConfig(
                reasons=[MatchFailureReason.MISSING_PROPERTY],
                source_pk=str(self.source.pk),
                stage_pk=str(stage.pk),
            ),
        )
        # Hijack flow plan so we don't have to emulate the source
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        plan.insert_stage(in_memory_stage(SourceStageFinal), index=0)
        plan.context[PLAN_CONTEXT_IS_RESTORED] = flow_token
        plan.context["foo"] = "bar"
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # Pretend we've just returned from the source
        with self.assertFlowFinishes() as ff:
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}), follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertStageRedirects(
                response, reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
            )
        self.assertEqual(ff().context["foo"], "bar")

    def test_source_expired_token(self):
        """Test returning from the source after the resume token expired"""
        flow, _, flow_token = self.run_to_source_redirect()
        flow_token.expires = now() - timedelta(seconds=1)
        flow_token.save(update_fields=("expires",))
        # Hijack flow plan so we don't have to emulate the source
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        plan.insert_stage(in_memory_stage(SourceStageFinal), index=0)
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # Pretend we've just returned from the source
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertStageResponse(response, component="ak-stage-access-denied")
        session = self.client.session
        self.assertNotIn(SESSION_KEY_OVERRIDE_FLOW_TOKEN, session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_STAGES, session)
        self.assertNotIn(SESSION_KEY_SOURCE_FLOW_CONTEXT, session)
