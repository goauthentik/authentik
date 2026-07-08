"""User switch view tests"""

from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.urls import reverse

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import (
    create_test_brand,
    create_test_flow,
    create_test_session,
    create_test_user,
)
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_USER_SWITCH_FROM_USER,
    PLAN_CONTEXT_USER_SWITCH_SESSION,
    PLAN_CONTEXT_USER_SWITCH_STALE_USER,
    FlowPlan,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.user_login.models import UserLoginStage


class TestUserSwitch(FlowTestCase):
    """Test starting the brand's user switch flow"""

    def setUp(self):
        super().setUp()
        self.user = create_test_user()
        self.other_user = create_test_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.login_binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=UserLoginStage.objects.create(name="login"),
            order=0,
        )
        self.brand = create_test_brand(flow_user_switch=self.flow)

    def switch_url(self, user) -> str:
        return reverse("authentik_core:user-switch", kwargs={"user_pk": user.pk})

    def login(self, user) -> str:
        """Log the test client in through the flow executor, returning the session key"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, bindings=[self.login_binding], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        return self.client.session.session_key

    def user_switching_token(self) -> str:
        """Return the decoded user switching token from the test client's cookie."""
        user_switching_token = user_switching.decode_cookie(
            self.client.cookies[user_switching.COOKIE_NAME].value
        )
        if user_switching_token is None:
            self.fail("Expected a user switching token cookie after login")
        return user_switching_token

    def test_no_brand_flow_disables_switching(self):
        """Test switching shows an error when the brand has no user switch flow"""
        self.brand.flow_user_switch = None
        self.brand.save()
        self.login(self.user)
        user_switching_token = self.user_switching_token()
        create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(
            self.switch_url(self.other_user),
            {"next": "/if/admin/#/core/brands"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "User switching is disabled.",
            status_code=400,
        )

    def test_no_brand_flow_does_not_redirect_to_next(self):
        """Test disabled switching renders the endpoint instead of redirecting to next"""
        self.brand.flow_user_switch = None
        self.brand.save()
        self.login(self.user)

        response = self.client.get(
            self.switch_url(self.other_user),
            {"next": "https://example.invalid/"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "User switching is disabled.",
            status_code=400,
        )

    def test_switch_requires_authenticated_source_user(self):
        """Test switching is rejected when there is no current login to switch from"""
        user_switching_token = "A" * 32
        self.client.cookies[user_switching.COOKIE_NAME] = user_switching.encode_cookie(
            user_switching_token
        )
        create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlsplit(response.url).path,
            reverse("authentik_flows:default-authentication"),
        )
        self.assertEqual(
            parse_qs(urlsplit(response.url).query)["next"],
            [self.switch_url(self.other_user)],
        )

    def test_switch_with_live_session(self):
        """Test a live login of this browser is passed to the flow as context"""
        self.login(self.user)
        user_switching_token = self.user_switching_token()
        target_session = create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.other_user)
        self.assertEqual(
            plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER],
            self.other_user.username,
        )
        self.assertEqual(plan.context[PLAN_CONTEXT_USER_SWITCH_FROM_USER], self.user)
        self.assertEqual(
            plan.context[PLAN_CONTEXT_USER_SWITCH_SESSION], target_session.session.session_key
        )

    def test_switch_rejects_target_session_deleted_after_planning(self):
        """Test a switch target is revalidated immediately before login."""
        first_session_key = self.login(self.user)
        user_switching_token = self.user_switching_token()
        target_session = create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(self.switch_url(self.other_user))
        self.assertEqual(response.status_code, 302)
        target_session.session.delete()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")
        self.assertEqual(self.client.session.session_key, first_session_key)
        current = AuthenticatedSession.objects.get(session__session_key=first_session_key)
        self.assertEqual(current.user, self.user)
        self.assertTrue(current.is_current)

    def test_switch_flow_must_apply_to_current_user(self):
        """Test switching rejects flows the source user cannot access."""
        self.login(self.user)
        user_switching_token = self.user_switching_token()
        create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )
        PolicyBinding.objects.create(target=self.flow, user=self.other_user, order=0)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 404)

    def test_switch_without_live_session(self):
        """Test an unknown or stale target starts the flow without switch context"""
        self.login(self.user)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER, plan.context)
        self.assertNotIn(PLAN_CONTEXT_USER_SWITCH_FROM_USER, plan.context)
        self.assertEqual(
            plan.context[PLAN_CONTEXT_USER_SWITCH_STALE_USER],
            str(self.other_user.pk),
        )

    def test_switch_ignores_other_browser_session(self):
        """Test a live login of a different browser doesn't count as proof"""
        self.login(self.user)
        create_test_session(self.other_user, user_switching_token="A" * 32)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER, plan.context)
        self.assertEqual(
            plan.context[PLAN_CONTEXT_USER_SWITCH_STALE_USER],
            str(self.other_user.pk),
        )

    def test_identification_stage_skips_prefilled_user(self):
        """Test a switch through an authentication flow doesn't ask for the
        username again and goes straight to the next stage"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        FlowStageBinding.objects.create(
            target=flow,
            stage=IdentificationStage.objects.create(
                name=f"{flow.slug}-identification",
                user_fields=["username"],
            ),
            order=10,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=f"{flow.slug}-next"),
            order=20,
        )
        self.brand.flow_user_switch = flow
        self.brand.save()
        self.login(self.user)
        user_switching_token = self.user_switching_token()
        create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(self.switch_url(self.other_user))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)

        self.assertStageResponse(response, flow, component="ak-stage-dummy")

    def test_full_switch(self):
        """Test the full switch: the new login takes over, the old session survives
        as a switch target but can't be replayed"""
        first_session_key = self.login(self.user)
        user_switching_token = self.user_switching_token()
        create_test_session(
            self.other_user, user_switching_token=user_switching_token, is_current=False
        )

        response = self.client.get(self.switch_url(self.other_user), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)

        # The client is now logged in as the other user on a new session
        self.assertNotEqual(self.client.session.session_key, first_session_key)
        current = AuthenticatedSession.objects.get(
            session__session_key=self.client.session.session_key
        )
        self.assertEqual(current.user, self.other_user)
        self.assertTrue(current.is_current)
        # The first user's login survives as a switch target, but is superseded
        first = AuthenticatedSession.objects.get(session__session_key=first_session_key)
        self.assertEqual(first.user, self.user)
        self.assertFalse(first.is_current)
        self.assertTrue(Session.objects.filter(session_key=first_session_key).exists())
        # The login is audited as a user switch from the first user
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            context__is_user_switch=True,
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.user["username"], self.other_user.username)
        self.assertEqual(
            event.context[PLAN_CONTEXT_USER_SWITCH_FROM_USER]["username"],
            self.user.username,
        )
        # Replaying the first session cookie doesn't authenticate anymore
        self.client.cookies[settings.SESSION_COOKIE_NAME] = first_session_key
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 403)
