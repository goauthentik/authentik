"""Account switch view tests"""

from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import (
    create_test_brand,
    create_test_flow,
    create_test_session,
    create_test_user,
)
from authentik.core.views.account_switch import QS_ACCOUNT_SWITCH_STALE
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import (
    PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER,
    PLAN_CONTEXT_IS_ACCOUNT_SWITCH,
    PLAN_CONTEXT_PENDING_USER,
    FlowPlan,
)
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.root.middleware import COOKIE_NAME_ACCOUNTS
from authentik.stages.user_login.models import UserLoginStage


class TestAccountSwitch(FlowTestCase):
    """Test starting the brand's account switch flow"""

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
        self.brand = create_test_brand(flow_account_switch=self.flow)

    def switch_url(self, user) -> str:
        return reverse("authentik_core:account-switch", kwargs={"user_uid": user.uid})

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

    def test_no_brand_flow_falls_back(self):
        """Test switching falls back to the default authentication flow"""
        self.brand.flow_account_switch = None
        self.brand.save()
        self.login(self.user)
        browser_key = self.client.cookies[COOKIE_NAME_ACCOUNTS].value
        create_test_session(self.other_user, browser_key=browser_key)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.other_user)

    def test_no_flow_at_all(self):
        """Test switching 404s when no authentication flow exists either"""
        self.brand.flow_account_switch = None
        self.brand.save()
        Flow.objects.filter(designation=FlowDesignation.AUTHENTICATION).delete()

        response = self.client.get(self.switch_url(self.user))

        self.assertEqual(response.status_code, 404)

    def test_switch_with_live_session(self):
        """Test a live login of this browser is passed to the flow as context"""
        self.login(self.user)
        browser_key = self.client.cookies[COOKIE_NAME_ACCOUNTS].value
        create_test_session(self.other_user, browser_key=browser_key)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.other_user)
        self.assertTrue(plan.context[PLAN_CONTEXT_IS_ACCOUNT_SWITCH])
        self.assertEqual(plan.context[PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER], self.user)

    def test_switch_without_live_session(self):
        """Test an unknown or stale target starts the flow without switch context"""
        self.login(self.user)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER, plan.context)
        self.assertNotIn(PLAN_CONTEXT_IS_ACCOUNT_SWITCH, plan.context)
        self.assertEqual(
            parse_qs(urlsplit(response.url).query)[QS_ACCOUNT_SWITCH_STALE],
            [self.other_user.uid],
        )

    def test_switch_ignores_other_browser_session(self):
        """Test a live login of a different browser doesn't count as proof"""
        self.login(self.user)
        create_test_session(self.other_user, browser_key="A" * 32)

        response = self.client.get(self.switch_url(self.other_user))

        self.assertEqual(response.status_code, 302)
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER, plan.context)
        self.assertEqual(
            parse_qs(urlsplit(response.url).query)[QS_ACCOUNT_SWITCH_STALE],
            [self.other_user.uid],
        )

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_default_flow_skips_identification(self):
        """Test a switch through the default authentication flow doesn't ask for the
        username again and goes straight to the password stage"""
        flow = Flow.objects.get(slug="default-authentication-flow")
        self.brand.flow_account_switch = flow
        self.brand.save()
        self.login(self.user)
        browser_key = self.client.cookies[COOKIE_NAME_ACCOUNTS].value
        create_test_session(self.other_user, browser_key=browser_key)

        response = self.client.get(self.switch_url(self.other_user))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)

        self.assertStageResponse(response, flow, component="ak-stage-password")

    def test_full_switch(self):
        """Test the full switch: the new login takes over, the old session survives
        as a switch target but can't be replayed"""
        first_session_key = self.login(self.user)
        browser_key = self.client.cookies[COOKIE_NAME_ACCOUNTS].value
        create_test_session(self.other_user, browser_key=browser_key)

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
        # The login is audited as an account switch from the first user
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            context__is_account_switch=True,
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.user["username"], self.other_user.username)
        self.assertEqual(
            event.context[PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER]["username"],
            self.user.username,
        )
        # Replaying the first session cookie doesn't authenticate anymore
        self.client.cookies[settings.SESSION_COOKIE_NAME] = first_session_key
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 403)
