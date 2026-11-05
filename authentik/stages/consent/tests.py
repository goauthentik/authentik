"""consent tests"""

from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.core.models import Application
from authentik.core.tasks import clean_expired_models
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.challenge import PermissionDict
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.tests import APIFlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.consent.models import ConsentClient, ConsentMode, ConsentStage, UserConsent
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_CLIENT,
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
    PLAN_CONTEXT_CONSENT_TOKEN,
)


class TestConsentStage(APIFlowTestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )

    def test_mismatched_token(self):
        """Test incorrect token"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.ALWAYS_REQUIRE)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": generate_id(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-consent",
            response_errors={
                "token": [{"string": "Invalid consent token, re-showing prompt", "code": "invalid"}]
            },
        )
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_always_required(self):
        """Test always required consent"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.ALWAYS_REQUIRE)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": self.get_flow_plan().context[PLAN_CONTEXT_CONSENT_TOKEN],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_permanent(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": self.get_flow_plan().context[PLAN_CONTEXT_CONSENT_TOKEN],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )

    def test_expire(self):
        """Test expiring consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(
            name=generate_id(), mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
        )
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={PLAN_CONTEXT_APPLICATION: self.application},
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
        with freeze_time() as frozen_time:
            frozen_time.tick(timedelta(seconds=3))
            clean_expired_models.send()
            self.assertFalse(
                UserConsent.objects.filter(user=self.user, application=self.application).exists()
            )

    def test_expire_reconsent(self):
        """Test consenting again after consent expired but before it was cleaned up"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(
            name=generate_id(), mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
        )
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)
        permissions = [PermissionDict(id="foo", name="foo-desc")]

        def consent():
            plan = FlowPlan(
                flow_pk=flow.pk.hex,
                bindings=[binding],
                markers=[StageMarker()],
                context={
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: permissions,
                },
            )
            session = self.client.session
            session[SESSION_KEY_PLAN] = plan
            session.save()
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            )
            raw_res = self.assertStageResponse(
                response,
                flow,
                self.user,
                permissions=[{"id": "foo", "name": "foo-desc"}],
                additional_permissions=[],
            )
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                {"token": raw_res["token"]},
            )
            self.assertEqual(response.status_code, 200)
            self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        consent()
        with freeze_time() as frozen_time:
            frozen_time.tick(timedelta(seconds=3))
            # The expired consent is hidden from the default manager, but still exists
            # as `clean_expired_models` hasn't run yet
            self.assertFalse(
                UserConsent.objects.filter(user=self.user, application=self.application).exists()
            )
            consent()
            self.assertEqual(
                UserConsent.objects.including_expired()
                .filter(user=self.user, application=self.application)
                .count(),
                1,
            )
            self.assertTrue(
                UserConsent.objects.filter(
                    user=self.user, application=self.application, permissions="foo"
                ).exists()
            )

    def test_permanent_more_perms(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [PermissionDict(id="foo", name="foo-desc")],
                PLAN_CONTEXT_CONSENT_HEADER: "test header",
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # First, consent with a single permission
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[
                {"id": "foo", "name": "foo-desc"},
            ],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions="foo"
            ).exists()
        )

        # Request again with more perms
        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [
                    PermissionDict(id="foo", name="foo-desc"),
                    PermissionDict(id="bar", name="bar-desc"),
                ],
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[
                {"id": "foo", "name": "foo-desc"},
            ],
            additional_permissions=[
                {"id": "bar", "name": "bar-desc"},
            ],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions="foo bar"
            ).exists()
        )

    def test_permanent_same(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # First, consent with a single permission
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions=""
            ).exists()
        )

        # Request again with the same perms
        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, component="xak-flow-redirect")


CLIENT_A = "https://a.example.com/oauth/client.json"
CLIENT_B = "https://b.example.com/oauth/client.json"
RESOURCE_A = "https://a.example.com/mcp"
RESOURCE_B = "https://b.example.com/mcp"


class TestConsentStageClients(APIFlowTestCase):
    """Consent given to a client of an application instead of the application itself"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=stage, order=2)
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def start(self, client: ConsentClient | None, permissions=("foo",)):
        """Plan the consent stage for `client`, return the first stage response"""
        context = {
            PLAN_CONTEXT_APPLICATION: self.application,
            PLAN_CONTEXT_CONSENT_PERMISSIONS: [
                PermissionDict(id=perm, name=f"{perm}-desc") for perm in permissions
            ],
        }
        if client:
            context[PLAN_CONTEXT_CONSENT_CLIENT] = client
        self.set_flow_plan(
            FlowPlan(
                flow_pk=self.flow.pk.hex,
                bindings=[self.binding],
                markers=[StageMarker()],
                context=context,
            )
        )
        return self.client.get(self.url)

    def consent(self, client: ConsentClient | None, permissions=("foo",)) -> dict:
        """Run the consent stage for `client` and accept the prompt, which must be shown"""
        response = self.start(client, permissions)
        challenge = self.assertStageResponse(response, component="ak-stage-consent")
        response = self.client.post(self.url, {"token": challenge["token"]})
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        return challenge

    def assertPrompted(self, client: ConsentClient | None, permissions=("foo",)) -> dict:
        response = self.start(client, permissions)
        return self.assertStageResponse(response, component="ak-stage-consent")

    def assertNotPrompted(self, client: ConsentClient | None, permissions=("foo",)):
        response = self.start(client, permissions)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_consent_stored_per_client(self):
        """Consent given to a client records the client and resource, and is reused"""
        client = ConsentClient(client_id=CLIENT_A, resource=RESOURCE_A)
        self.consent(client)
        consent = UserConsent.objects.get(user=self.user, application=self.application)
        self.assertEqual(consent.client_id, CLIENT_A)
        self.assertEqual(consent.resource, RESOURCE_A)
        self.assertEqual(consent.binding_hash, client.binding_hash)
        self.assertEqual(consent.permissions, "foo")
        self.assertNotPrompted(client)

    def test_application_consent_never_authorizes_client(self):
        """Consent given to the application does not apply to its other clients"""
        self.consent(None)
        self.assertNotPrompted(None)
        self.assertPrompted(ConsentClient(client_id=CLIENT_A))

    def test_client_consent_never_authorizes_other_client(self):
        """Consent given to client A applies neither to client B nor to the application"""
        self.consent(ConsentClient(client_id=CLIENT_A))
        self.assertPrompted(ConsentClient(client_id=CLIENT_B))
        self.assertPrompted(None)
        self.consent(ConsentClient(client_id=CLIENT_B))
        self.assertEqual(
            sorted(
                UserConsent.objects.filter(application=self.application).values_list(
                    "client_id", flat=True
                )
            ),
            [CLIENT_A, CLIENT_B],
        )

    def test_resource_expansion_prompts(self):
        """Consent for one resource does not cover another, or none"""
        self.consent(ConsentClient(client_id=CLIENT_A, resource=RESOURCE_A))
        self.assertPrompted(ConsentClient(client_id=CLIENT_A, resource=RESOURCE_B))
        self.assertPrompted(ConsentClient(client_id=CLIENT_A))

    def test_scope_expansion_prompts(self):
        """Requesting more permissions prompts for only the new ones, and updates consent"""
        client = ConsentClient(client_id=CLIENT_A)
        self.consent(client)
        challenge = self.assertPrompted(client, ("foo", "bar"))
        self.assertEqual(challenge["permissions"], [{"id": "foo", "name": "foo-desc"}])
        self.assertEqual(challenge["additional_permissions"], [{"id": "bar", "name": "bar-desc"}])
        response = self.client.post(self.url, {"token": challenge["token"]})
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        consent = UserConsent.objects.get(user=self.user, application=self.application)
        self.assertEqual(consent.client_id, CLIENT_A)
        self.assertEqual(consent.permissions, "foo bar")

    def test_challenge_client_fields(self):
        """The challenge identifies a client; challenges for the application are unchanged"""
        challenge = self.assertPrompted(
            ConsentClient(client_id=CLIENT_A, name="Client A", redirect_host="127.0.0.1")
        )
        self.assertEqual(challenge["client_id"], CLIENT_A)
        self.assertEqual(challenge["client_name"], "Client A")
        self.assertEqual(challenge["redirect_host"], "127.0.0.1")
        challenge = self.assertPrompted(ConsentClient(client_id=CLIENT_A))
        self.assertEqual(challenge["client_id"], CLIENT_A)
        self.assertNotIn("client_name", challenge)
        self.assertNotIn("redirect_host", challenge)
        challenge = self.assertPrompted(None)
        for field in ("client_id", "client_name", "redirect_host"):
            self.assertNotIn(field, challenge)

    def test_expired_client_consent_replaced(self):
        """Expired consent of a client is replaced without touching other consent"""
        client = ConsentClient(client_id=CLIENT_A)
        other = UserConsent.objects.create(
            user=self.user,
            application=self.application,
            permissions="foo",
            expires=now() - timedelta(days=1),
        )
        UserConsent.objects.create(
            user=self.user,
            application=self.application,
            permissions="foo",
            client_id=CLIENT_A,
            expires=now() - timedelta(days=1),
        )
        self.consent(client)
        consent = UserConsent.objects.get(user=self.user, client_id=CLIENT_A)
        self.assertFalse(consent.expiring)
        self.assertTrue(UserConsent.objects.including_expired().filter(pk=other.pk).exists())

    def test_hash_collision_does_not_match(self):
        """A consent whose hash matches but whose client differs is not used"""
        client = ConsentClient(client_id=CLIENT_A)
        UserConsent.objects.create(
            user=self.user,
            application=self.application,
            permissions="foo",
            client_id=CLIENT_B,
            expiring=False,
        )
        UserConsent.objects.filter(client_id=CLIENT_B).update(binding_hash=client.binding_hash)
        self.assertPrompted(client)

    def test_api_lists_and_revokes_client_consent(self):
        """Users list consent per client and revoke it without affecting other clients"""
        self.consent(ConsentClient(client_id=CLIENT_A, resource=RESOURCE_A))
        self.consent(ConsentClient(client_id=CLIENT_B))
        response = self.client.get(
            reverse("authentik_api:userconsent-list"),
            {"client_id": CLIENT_A},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["client_id"], CLIENT_A)
        self.assertEqual(results[0]["resource"], RESOURCE_A)
        response = self.client.delete(
            reverse(
                "authentik_api:userconsent-detail",
                kwargs={"pk": results[0]["pk"]},
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertPrompted(ConsentClient(client_id=CLIENT_A, resource=RESOURCE_A))
        self.assertNotPrompted(ConsentClient(client_id=CLIENT_B))
