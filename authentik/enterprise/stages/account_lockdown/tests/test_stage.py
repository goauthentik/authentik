"""Account lockdown stage tests"""

import json
from dataclasses import asdict
from threading import Event as ThreadEvent
from threading import Thread
from types import SimpleNamespace
from unittest.mock import patch

from django.db import connection
from django.http import HttpResponse
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from authentik.core.models import AuthenticatedSession, Session, Token, TokenIntents
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.enterprise.stages.account_lockdown.stage import (
    PLAN_CONTEXT_LOCKDOWN_REASON,
    QS_LOCKDOWN_USER,
    AccountLockdownStageView,
    can_lock_user,
)
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    DeviceToken,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
)
from authentik.providers.saml.models import SAMLProvider, SAMLSession
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

patch_enterprise_enabled = patch(
    "authentik.enterprise.apps.AuthentikEnterpriseConfig.check_enabled",
    return_value=True,
)


class AccountLockdownStageTestMixin:
    """Shared setup helpers for account lockdown stage tests."""

    @classmethod
    def setUpClass(cls):
        cls.patch_enterprise_enabled = patch_enterprise_enabled.start()
        cls.patch_event_dispatch = patch("authentik.events.tasks.event_trigger_dispatch.send")
        cls.patch_event_dispatch.start()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.patch_event_dispatch.stop()
        patch_enterprise_enabled.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.target_user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.stage = AccountLockdownStage.objects.create(
            name="lockdown",
            self_service_message_title="Your account has been locked",
            self_service_message_body="<p>Your account has been locked.</p>",
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.request_factory = RequestFactory()

    def make_stage_view(self, plan: FlowPlan):
        def _stage_ok():
            return HttpResponse(status=204)

        def _stage_invalid(_error_message=None):
            return HttpResponse(status=400)

        return AccountLockdownStageView(
            SimpleNamespace(
                plan=plan,
                current_stage=self.stage,
                current_binding=self.binding,
                flow=self.flow,
                stage_ok=_stage_ok,
                stage_invalid=_stage_invalid,
            )
        )

    def make_request(self, *, user=None, query=None):
        return self.request_factory.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            query_params=query or {},
            user=user,
        )


class TestAccountLockdownStage(AccountLockdownStageTestMixin, FlowTestCase):
    """Account lockdown stage tests"""

    def test_lockdown_no_target(self):
        """Test lockdown stage with no target user fails"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)

        self.assertIsNone(view.get_target_user(self.make_request()))

    def test_lockdown_with_query_target(self):
        """Test lockdown stage with a query-param target."""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_REASON] = "Security incident"
        view = self.make_stage_view(plan)
        request = self.make_request(
            user=self.user, query={QS_LOCKDOWN_USER: str(self.target_user.pk)}
        )
        target = view.get_target_user(request)
        self.assertEqual(target.pk, self.target_user.pk)
        self.assertTrue(can_lock_user(request.user, target))
        view._lockdown_user(request, self.stage, target, view.get_reason())

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertFalse(self.target_user.has_usable_password())

        # Check event was created
        event = Event.objects.filter(action=EventAction.USER_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "Security incident")
        self.assertEqual(event.context["affected_user"], self.target_user.username)

    def test_lockdown_with_query_target_reason(self):
        """Test lockdown stage with a query-param target and explicit reason."""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_REASON] = "Compromised account"
        view = self.make_stage_view(plan)
        request = self.make_request(
            user=self.user,
            query={QS_LOCKDOWN_USER: str(self.target_user.pk)},
        )
        target = view.get_target_user(request)
        self.assertEqual(target.pk, self.target_user.pk)
        self.assertTrue(can_lock_user(request.user, target))
        view._lockdown_user(request, self.stage, target, view.get_reason())

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_lockdown_reason_from_prompt(self):
        """Test lockdown stage reads the reason from prompt data."""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {
            PLAN_CONTEXT_LOCKDOWN_REASON: "User requested lockdown",
        }
        view = self.make_stage_view(plan)
        request = self.make_request(user=self.user)
        view._lockdown_user(request, self.stage, self.target_user, view.get_reason())

        event = Event.objects.filter(action=EventAction.USER_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "User requested lockdown")

    def test_lockdown_event_failure_does_not_fail_self_service(self):
        """Test lockdown still succeeds when event emission fails."""
        self.stage.delete_sessions = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        request = self.make_request(
            user=self.target_user, query={QS_LOCKDOWN_USER: str(self.target_user.pk)}
        )

        original_event_new = Event.new

        def _event_new_side_effect(action, *args, **kwargs):
            if action == EventAction.USER_LOCKDOWN_TRIGGERED:
                raise RuntimeError("simulated event failure")
            return original_event_new(action, *args, **kwargs)

        with patch(
            "authentik.enterprise.stages.account_lockdown.stage.Event.new",
            side_effect=_event_new_side_effect,
        ):
            view._lockdown_user(request, self.stage, self.target_user, view.get_reason())

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_dispatch_records_success_when_event_emission_fails(self):
        """Test dispatch still completes if event emission fails."""
        self.stage.delete_sessions = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        request = self.make_request(
            user=self.target_user, query={QS_LOCKDOWN_USER: str(self.target_user.pk)}
        )

        original_event_new = Event.new

        def _event_new_side_effect(action, *args, **kwargs):
            if action == EventAction.USER_LOCKDOWN_TRIGGERED:
                raise RuntimeError("simulated event failure")
            return original_event_new(action, *args, **kwargs)

        with patch(
            "authentik.enterprise.stages.account_lockdown.stage.Event.new",
            side_effect=_event_new_side_effect,
        ):
            response = view.dispatch(request)

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertEqual(response.status_code, 204)

    def test_lockdown_self_service_redirects_to_completion_flow(self):
        """Test self-service lockdown redirects to completion flow when sessions are deleted."""
        completion_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.stage.self_service_completion_flow = completion_flow
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        request = self.make_request(user=self.target_user)
        view._lockdown_user(request, self.stage, self.target_user, view.get_reason())
        response = view._self_service_completion_response(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": completion_flow.slug}),
        )

    def test_lockdown_self_service_requires_completion_flow(self):
        """Test self-service lockdown fails before deleting sessions without a completion flow."""
        self.stage.self_service_completion_flow = None
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        request = self.make_request(
            user=self.target_user, query={QS_LOCKDOWN_USER: str(self.target_user.pk)}
        )

        response = view.dispatch(request)

        self.assertEqual(response.status_code, 400)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)

    def test_lockdown_denies_other_user_without_permission(self):
        """Test lockdown stage rejects non-self requests without change_user permission."""
        actor = create_test_user()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        request = self.make_request(user=actor, query={QS_LOCKDOWN_USER: str(self.target_user.pk)})
        target = view.get_target_user(request)

        self.assertEqual(target.pk, self.target_user.pk)
        self.assertFalse(can_lock_user(request.user, target))

    def test_lockdown_revokes_tokens(self):
        """Test lockdown stage revokes tokens"""
        Token.objects.create(
            user=self.target_user,
            identifier="test-token",
            intent=TokenIntents.INTENT_API,
            key=generate_id(),
            expiring=False,
        )
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 1)

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        view._lockdown_user(self.make_request(user=self.user), self.stage, self.target_user, "")

        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 0)

    def test_lockdown_revokes_provider_tokens(self):
        """Test lockdown stage revokes provider tokens and sessions."""
        oauth_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/callback")
            ],
            signing_key=create_test_cert(),
        )
        saml_provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="https://sp.example.com/acs",
            issuer="https://idp.example.com",
        )
        session = Session.objects.create(
            session_key=generate_id(),
            expires=timezone.now() + timezone.timedelta(hours=1),
            last_ip="127.0.0.1",
        )
        auth_session = AuthenticatedSession.objects.create(
            session=session,
            user=self.target_user,
        )
        grant_kwargs = {
            "provider": oauth_provider,
            "user": self.target_user,
            "auth_time": timezone.now(),
            "_scope": "openid profile",
            "expiring": False,
        }
        token_kwargs = grant_kwargs | {"_id_token": json.dumps(asdict(IDToken("foo", "bar")))}
        AuthorizationCode.objects.create(
            code=generate_id(),
            session=auth_session,
            **grant_kwargs,
        )
        AccessToken.objects.create(
            token=generate_id(),
            session=auth_session,
            **token_kwargs,
        )
        RefreshToken.objects.create(
            token=generate_id(),
            session=auth_session,
            **token_kwargs,
        )
        DeviceToken.objects.create(
            provider=oauth_provider,
            user=self.target_user,
            session=auth_session,
            _scope="openid profile",
            expiring=False,
        )
        SAMLSession.objects.create(
            provider=saml_provider,
            user=self.target_user,
            session=auth_session,
            session_index=generate_id(),
            name_id=self.target_user.email,
            expires=timezone.now() + timezone.timedelta(hours=1),
            expiring=True,
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        view._lockdown_user(self.make_request(user=self.user), self.stage, self.target_user, "")

        self.assertEqual(AuthorizationCode.objects.filter(user=self.target_user).count(), 0)
        self.assertEqual(AccessToken.objects.filter(user=self.target_user).count(), 0)
        self.assertEqual(RefreshToken.objects.filter(user=self.target_user).count(), 0)
        self.assertEqual(DeviceToken.objects.filter(user=self.target_user).count(), 0)
        self.assertEqual(SAMLSession.objects.filter(user=self.target_user).count(), 0)

    def test_lockdown_selective_actions(self):
        """Test lockdown stage with selective actions"""
        self.stage.deactivate_user = True
        self.stage.set_unusable_password = False
        self.stage.delete_sessions = False
        self.stage.revoke_tokens = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.set_password("testpassword")
        self.target_user.save()

        Token.objects.create(
            user=self.target_user,
            identifier="test-token",
            intent=TokenIntents.INTENT_API,
            key=generate_id(),
            expiring=False,
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        view._lockdown_user(self.make_request(user=self.user), self.stage, self.target_user, "")

        self.target_user.refresh_from_db()
        # User should be deactivated
        self.assertFalse(self.target_user.is_active)
        # Password should still be usable
        self.assertTrue(self.target_user.has_usable_password())
        # Token should still exist
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 1)

    def test_lockdown_no_actions(self):
        """Test lockdown stage with all actions disabled"""
        self.stage.deactivate_user = False
        self.stage.set_unusable_password = False
        self.stage.delete_sessions = False
        self.stage.revoke_tokens = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.set_password("testpassword")
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        view._lockdown_user(self.make_request(user=self.user), self.stage, self.target_user, "")

        self.target_user.refresh_from_db()
        # User should still be active
        self.assertTrue(self.target_user.is_active)
        # Password should still be usable
        self.assertTrue(self.target_user.has_usable_password())
        # Event should still be created
        event = Event.objects.filter(action=EventAction.USER_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)


class TestAccountLockdownStageConcurrency(AccountLockdownStageTestMixin, TransactionTestCase):
    """Account lockdown concurrency tests."""

    def test_lockdown_retries_when_another_transaction_recreates_a_token(self):
        """Lockdown should remove a token recreated before the retry check runs."""
        Token.objects.create(
            user=self.target_user,
            identifier=f"initial-token-{generate_id()}",
            intent=TokenIntents.INTENT_API,
            key=generate_id(),
            expiring=False,
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        view = self.make_stage_view(plan)
        original_has_artifacts = view._has_lockdown_artifacts
        target_user = self.target_user
        thread_ready = ThreadEvent()
        start_create = ThreadEvent()
        thread_done = ThreadEvent()
        thread_errors = []

        class TokenCreatorThread(Thread):
            __test__ = False

            def run(self):
                try:
                    thread_ready.set()
                    if not start_create.wait(timeout=5):
                        thread_errors.append("timed out waiting to recreate token")
                        return
                    Token.objects.create(
                        user=target_user,
                        identifier=f"concurrent-token-{generate_id()}",
                        intent=TokenIntents.INTENT_API,
                        key=generate_id(),
                        expiring=False,
                    )
                except Exception as exc:  # noqa: BLE001
                    thread_errors.append(exc)
                finally:
                    thread_done.set()
                    connection.close()

        def has_artifacts_after_concurrent_create(stage, user):
            if not start_create.is_set():
                start_create.set()
                self.assertTrue(
                    thread_done.wait(timeout=30),
                    (
                        "Concurrent token creation did not complete "
                        f"before retry check: {thread_errors}"
                    ),
                )
            return original_has_artifacts(stage, user)

        creator = TokenCreatorThread()
        with patch.object(
            view, "_has_lockdown_artifacts", side_effect=has_artifacts_after_concurrent_create
        ):
            creator.start()
            self.assertTrue(
                thread_ready.wait(timeout=5),
                "Concurrent token creation thread did not start",
            )
            view._lockdown_user(self.make_request(user=self.user), self.stage, self.target_user, "")
            creator.join()

        self.assertEqual(thread_errors, [])
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 0)
