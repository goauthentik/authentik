from django.urls import reverse
from freezegun import freeze_time
from rest_framework.test import APIClient

from authentik.brands.models import Brand
from authentik.core.models import (
    ActorPolicyInheritance,
    Application,
    Group,
    Token,
    TokenIntents,
    default_token_duration,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.requests.models import (
    ApplicationTemplate,
    GrantRequest,
    GrantRequestTarget,
    RequestedApplication,
    RequestRule,
    RequestRuleBinding,
    RequestStatus,
)
from authentik.enterprise.tests import enterprise_test
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.tests import APIFlowTestCase
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.test_api import TEST_DSA_CERT, TEST_DSA_KEY

REDIRECT_URI = "https://grafana.example.com/login/generic_oauth"


class ApplicationRequestTests(APIFlowTestCase):

    def setUp(self):
        self.requester = create_test_user()
        self.reviewer = create_test_user()
        for perm in ("view", "fulfill", "revoke"):
            self.reviewer.assign_perms_to_managed_role(f"authentik_requests.{perm}_grantrequest")
        self.engineering = Group.objects.create(name=f"engineering-{generate_id()}")
        self.support = Group.objects.create(name=f"support-{generate_id()}")
        self.mapping = ScopeMapping.objects.create(
            name=generate_id(), scope_name="openid", expression="return {}"
        )
        self.template = ApplicationTemplate.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            allowed_grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.CLIENT_CREDENTIALS],
            application_group="Self-served",
        )
        self.template.property_mappings.set([self.mapping])
        self.template.bindable_groups.set([self.engineering])
        self.rule = RequestRule.objects.create(name=generate_id())
        PolicyBinding.objects.create(target=self.rule, user=self.reviewer, order=0)
        rule_binding = RequestRuleBinding.objects.create(rule=self.rule, target=self.template)
        PolicyBinding.objects.create(target=rule_binding, user=self.requester, order=0)

    def _application(self, **overrides) -> dict:
        return {
            "name": "Grafana",
            "client_type": ClientType.CONFIDENTIAL,
            "redirect_uris": [REDIRECT_URI],
            "grant_types": [GrantType.AUTHORIZATION_CODE],
            "groups": [str(self.engineering.pk)],
            **overrides,
        }

    def _submit(self, application: dict | None, pbms: list | None = None):
        self.client.force_login(self.requester)
        return self.client.post(
            reverse("authentik_api:grantrequest-list"),
            data={"pbms": pbms or [str(self.template.pbm_uuid)], "application": application},
            format="json",
        )

    def _pending_request(self, **overrides) -> GrantRequest:
        """A pending application request, as the request flow's final stage stores it"""
        req = GrantRequest.objects.create(created_by=self.requester)
        GrantRequestTarget.objects.create(request=req, target=self.template)
        application = self._application(**overrides)
        groups = application.pop("groups")
        requested = RequestedApplication.objects.create(request=req, **application)
        requested.groups.set(groups)
        return req

    def _fulfill(self, req: GrantRequest, status: RequestStatus, reviewer=None):
        self.client.force_login(reviewer or self.reviewer)
        return self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": status, "data": {}},
        )

    def test_submit_stores_request_without_creating_anything(self):
        """Submitting runs the request flow and stores what was asked for, and nothing else"""
        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.STAGE_CONFIGURATION,
        )
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = flow
        brand.save()

        res = self._submit(self._application())
        self.assertEqual(res.status_code, 200, res.content)
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}), follow=True
        )
        self.assertStageResponse(res, component="xak-flow-redirect")

        requested = RequestedApplication.objects.get(request__created_by=self.requester)
        self.assertEqual(requested.name, "Grafana")
        self.assertEqual(requested.redirect_uris, [REDIRECT_URI])
        self.assertEqual(list(requested.groups.all()), [self.engineering])
        self.assertEqual(requested.template, self.template)
        self.assertEqual(requested.request.status, RequestStatus.CREATED)
        self.assertIsNone(requested.application)
        self.assertFalse(Application.objects.filter(name="Grafana").exists())

    def test_submit_rejects_what_the_template_does_not_allow(self):
        for application, field in (
            (self._application(groups=[str(self.support.pk)]), "groups"),
            (self._application(groups=[]), "groups"),
            (self._application(grant_types=[GrantType.IMPLICIT]), "grant_types"),
            (
                self._application(
                    client_type=ClientType.PUBLIC, grant_types=[GrantType.CLIENT_CREDENTIALS]
                ),
                "grant_types",
            ),
            (self._application(redirect_uris=[]), "redirect_uris"),
            (self._application(redirect_uris=["javascript:alert(1)"]), "redirect_uris"),
            (self._application(redirect_uris=["/callback"]), "redirect_uris"),
            (self._application(meta_launch_url="javascript:alert(1)"), "meta_launch_url"),
            # Placeholders the library fills with each viewer's data
            (
                self._application(meta_launch_url="https://grafana.example.com/?a=%(email)s"),
                "meta_launch_url",
            ),
            (
                self._application(redirect_uris=[f"{REDIRECT_URI}?a=%(attributes)s"]),
                "redirect_uris",
            ),
        ):
            with self.subTest(application=application):
                res = self._submit(application)
                self.assertEqual(res.status_code, 400, res.content)
                self.assertIn(field, res.json()["application"])
        self.assertFalse(GrantRequest.objects.filter(created_by=self.requester).exists())

    def test_submit_client_credentials_needs_no_redirect_uri(self):
        brand, _ = Brand.objects.get_or_create(default=True, defaults={"domain": generate_id()})
        brand.flow_request = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        brand.save()
        res = self._submit(
            self._application(redirect_uris=[], grant_types=[GrantType.CLIENT_CREDENTIALS])
        )
        self.assertEqual(res.status_code, 200, res.content)

    def test_submit_application_and_template_must_go_together(self):
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=self.rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=self.requester, order=0)

        res = self._submit(None)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("application", res.json())

        res = self._submit(self._application(), pbms=[str(app.pk)])
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("application", res.json())

        res = self._submit(self._application(), pbms=[str(self.template.pbm_uuid), str(app.pk)])
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("pbms", res.json())

    def test_approve_creates_application_from_template(self):
        req = self._pending_request()

        res = self._fulfill(req, RequestStatus.APPROVED)
        self.assertEqual(res.status_code, 204, res.content)

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.assertFalse(req.expiring)
        app = RequestedApplication.objects.get(request=req).application
        self.assertEqual(app.name, "Grafana")
        self.assertEqual(app.group, "Self-served")
        provider = OAuth2Provider.objects.get(application=app)
        self.assertEqual(provider.authorization_flow, self.template.authorization_flow)
        self.assertEqual(provider.invalidation_flow, self.template.invalidation_flow)
        self.assertEqual(
            list(provider.property_mappings.values_list("pk", flat=True)), [self.mapping.pk]
        )
        self.assertEqual(provider.client_type, ClientType.CONFIDENTIAL)
        self.assertEqual(provider.grant_types, [GrantType.AUTHORIZATION_CODE])
        self.assertEqual(
            provider.redirect_uris,
            [RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url=REDIRECT_URI)],
        )
        self.assertEqual(
            list(PolicyBinding.objects.filter(target=app).values_list("group", "user")),
            [(self.engineering.pk, None)],
        )
        event = Event.objects.get(
            action=EventAction.ACCESS_REQUEST_APPROVED, context__model__pk=req.pk.hex
        )
        self.assertEqual(event.context["application"]["pk"], app.pk.hex)

    def test_approve_rechecks_the_template(self):
        """A template changed after the request was made blocks approval and keeps the request
        pending, instead of creating something the template no longer allows"""
        req = self._pending_request()
        self.template.bindable_groups.set([self.support])

        res = self._fulfill(req, RequestStatus.APPROVED)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("groups", res.json())

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)
        self.assertFalse(req.approvals.exists())
        self.assertFalse(OAuth2Provider.objects.filter(name="Grafana").exists())

    def test_approve_after_template_deleted(self):
        req = self._pending_request()
        self.template.delete()

        res = self._fulfill(req, RequestStatus.APPROVED)
        self.assertEqual(res.status_code, 400, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)

    @enterprise_test()
    def test_agent_cannot_request_from_template(self):
        agent = Agent.create_for_user(
            self.requester,
            expiring=True,
            expires=default_token_duration(),
            policy_behavior=ActorPolicyInheritance.NONE,
        )
        token = Token.objects.create(
            identifier=agent.username,
            intent=TokenIntents.INTENT_API,
            user=agent,
            expiring=True,
            expires=default_token_duration(),
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        res = client.post(
            reverse("authentik_api:grantrequest-agent"),
            data={"pbms": [str(self.template.pbm_uuid)]},
            format="json",
        )
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(GrantRequest.objects.filter(created_by=agent).exists())

    def test_approve_picks_free_slug_and_provider_name(self):
        Application.objects.create(name="Grafana", slug="grafana")
        OAuth2Provider.objects.create(name="Grafana", authorization_flow=create_test_flow())
        req = self._pending_request()

        self.assertEqual(self._fulfill(req, RequestStatus.APPROVED).status_code, 204)

        app = RequestedApplication.objects.get(request=req).application
        self.assertEqual(app.slug, "grafana-2")
        self.assertEqual(app.provider.name, "Grafana-2")

    def test_approve_skips_reserved_slug(self):
        """A slug the OAuth2 provider's own URLs use is never given to an application"""
        req = self._pending_request(name="Token")

        self.assertEqual(self._fulfill(req, RequestStatus.APPROVED).status_code, 204)

        app = RequestedApplication.objects.get(request=req).application
        self.assertEqual(app.slug, "token-2")

    def test_deny_creates_nothing(self):
        req = self._pending_request()

        self.assertEqual(self._fulfill(req, RequestStatus.DENIED).status_code, 204)

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.DENIED)
        self.assertIsNone(RequestedApplication.objects.get(request=req).application)
        self.assertFalse(OAuth2Provider.objects.filter(name="Grafana").exists())

    def test_create_once_all_reviewers_approved(self):
        second_reviewer = create_test_user()
        second_reviewer.assign_perms_to_managed_role("authentik_requests.fulfill_grantrequest")
        second_reviewer.assign_perms_to_managed_role("authentik_requests.view_grantrequest")
        reviewers = Group.objects.create(name=generate_id())
        reviewers.users.add(self.reviewer, second_reviewer)
        PolicyBinding.objects.filter(target=self.rule).delete()
        PolicyBinding.objects.create(target=self.rule, group=reviewers, order=0)
        self.rule.min_reviewers = 2
        self.rule.save()
        req = self._pending_request()

        self.assertEqual(self._fulfill(req, RequestStatus.APPROVED).status_code, 204)
        self.assertFalse(OAuth2Provider.objects.filter(name="Grafana").exists())

        res = self._fulfill(req, RequestStatus.APPROVED, reviewer=second_reviewer)
        self.assertEqual(res.status_code, 204)
        self.assertEqual(OAuth2Provider.objects.filter(name="Grafana").count(), 1)

    def test_credentials_only_for_the_requester(self):
        req = self._pending_request()
        self.requester.assign_perms_to_managed_role("authentik_requests.view_grantrequest", req)
        url = reverse("authentik_api:grantrequest-credentials", kwargs={"pk": req.pk})

        self.client.force_login(self.requester)
        self.assertEqual(self.client.get(url).status_code, 404)

        self._fulfill(req, RequestStatus.APPROVED)
        provider = OAuth2Provider.objects.get(application__name="Grafana")

        self.client.force_login(self.requester)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        self.assertEqual(body["client_id"], provider.client_id)
        self.assertEqual(body["client_secret"], provider.client_secret)
        self.assertIn("issuer", body["urls"])

        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_credentials_of_the_created_provider_only(self):
        """Pointing the application at another provider later must not hand the requester
        that provider's secret"""
        req = self._pending_request()
        self.requester.assign_perms_to_managed_role("authentik_requests.view_grantrequest", req)
        self._fulfill(req, RequestStatus.APPROVED)
        app = RequestedApplication.objects.get(request=req).application
        created = OAuth2Provider.objects.get(application=app)
        other = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        app.provider = other
        app.save()

        self.client.force_login(self.requester)
        res = self.client.get(
            reverse("authentik_api:grantrequest-credentials", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["client_id"], created.client_id)
        self.assertNotEqual(res.json()["client_secret"], other.client_secret)

    def test_credentials_omit_secret_of_public_client(self):
        req = self._pending_request(client_type=ClientType.PUBLIC)
        self.requester.assign_perms_to_managed_role("authentik_requests.view_grantrequest", req)
        self._fulfill(req, RequestStatus.APPROVED)

        self.client.force_login(self.requester)
        res = self.client.get(
            reverse("authentik_api:grantrequest-credentials", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIsNone(res.json()["client_secret"])

    def test_revoke_refused(self):
        req = self._pending_request()
        self._fulfill(req, RequestStatus.APPROVED)

        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 400, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)

    def test_requestable_templates(self):
        url = reverse("authentik_api:applicationtemplate-requestable")

        self.client.force_login(self.requester)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200, res.content)
        (result,) = res.json()["results"]
        self.assertEqual(result["name"], self.template.name)
        self.assertEqual(
            result["bindable_groups_obj"],
            [{"pk": str(self.engineering.pk), "name": self.engineering.name}],
        )

        self.client.force_login(create_test_user())
        self.assertEqual(self.client.get(url).json()["results"], [])

    @enterprise_test()
    @freeze_time("2022-10-14T14:15:00Z")
    def test_template_refuses_unsupported_signing_key(self):
        """Providers created from the template could not sign tokens with this key"""
        cert = CertificateKeyPair.objects.create(
            name=generate_id(), certificate_data=TEST_DSA_CERT, key_data=TEST_DSA_KEY
        )
        self.client.force_login(create_test_admin_user())
        res = self.client.patch(
            reverse("authentik_api:applicationtemplate-detail", kwargs={"pk": self.template.pk}),
            data={"signing_key": str(cert.pk)},
            format="json",
        )
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("signing_key", res.json())

    @enterprise_test()
    def test_template_needs_bindable_groups(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:applicationtemplate-list"),
            data={
                "name": generate_id(),
                "authorization_flow": str(create_test_flow().pk),
                "invalidation_flow": str(create_test_flow().pk),
                "allowed_grant_types": [GrantType.AUTHORIZATION_CODE],
                "bindable_groups": [],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn("bindable_groups", res.json())
