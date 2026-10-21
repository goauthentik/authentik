from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APIClient, APITestCase

from authentik.core.models import (
    ActorPolicyInheritance,
    Application,
    ApplicationEntitlement,
    Token,
    TokenIntents,
    User,
    UserTypes,
    default_token_duration,
)
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.requests.models import (
    GrantRequest,
    RequestRule,
    RequestRuleBinding,
    RequestStatus,
)
from authentik.enterprise.tests import enterprise_test
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel


@enterprise_test()
class AgentGrantRequestTests(APITestCase):
    """An agent inherits no access, so it earns it by asking its owner to delegate some. It may
    only ask for what the owner already holds -- no flow runs on this path, so there is no
    justification to hand a reviewer -- and the owner's approval is the whole decision."""

    def _app(self) -> Application:
        return Application.objects.create(name=generate_id(), slug=generate_id())

    def _entitlement(self, app: Application) -> ApplicationEntitlement:
        return ApplicationEntitlement.objects.create(app=app, name=generate_id())

    def _agent_for(self, owner: User) -> tuple[Agent, APIClient]:
        """A self-service-shaped agent (no inherited access) plus a client authenticating
        as it, exactly as a harness holding the agent's API token would."""
        agent = Agent.create_for_user(
            owner,
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
        return agent, client

    def _request_access(self, client: APIClient, *pbms):
        return client.post(
            reverse("authentik_api:grantrequest-agent"),
            data={"pbms": [str(pbm.pk) for pbm in pbms]},
            format="json",
        )

    def _fulfill(self, user: User, req: GrantRequest, status: str = "approved"):
        self.client.force_login(user)
        return self.client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": status, "data": {}},
        )

    def _requestable_by(
        self, target: PolicyBindingModel, requester: User, reviewer: User
    ) -> RequestRule:
        """Wire `target` up so `requester` may request it and `reviewer` may approve."""
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=target)
        PolicyBinding.objects.create(target=rule_binding, user=requester, order=0)
        PolicyBinding.objects.create(target=rule, user=reviewer, order=0)
        return rule

    def test_owner_already_has_access_owner_approval_suffices(self):
        """The owner can already reach the target, so there is nothing for reviewers to
        decide -- the owner's own approval grants the agent access."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)

        # The agent starts with nothing, even though its owner passes.
        self.assertTrue(PolicyEngine(app, owner).build().passing)
        self.assertFalse(PolicyEngine(app, agent).build().passing)

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 201, res.content)
        req = GrantRequest.objects.get(pk=res.json()["grant_request"]["uuid"])
        self.assertEqual(req.created_by_id, agent.pk)
        self.assertEqual(req.agent_owner_id, owner.pk)

        res = self._fulfill(owner, req)
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        # The grant lands on the agent, not on the owner who approved it.
        self.assertTrue(PolicyBinding.objects.filter(user=agent, target=app).exists())
        self.assertTrue(PolicyEngine(app, agent).build().passing)

    def test_response_carries_fulfill_url_for_the_owner(self):
        """An agent has no browser, so it gets back the URL its owner opens to act on the
        request -- the same deep link the created event points at."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        _, agent_client = self._agent_for(owner)

        body = self._request_access(agent_client, app).json()
        req = GrantRequest.objects.get(pk=body["grant_request"]["uuid"])
        # Absolute, so it is usable verbatim by whatever the agent hands it to.
        self.assertTrue(body["fulfill_url"].startswith("http"))
        self.assertTrue(
            body["fulfill_url"].endswith(f"#/requests/access-request/{req.uuid}/fulfill"),
            body["fulfill_url"],
        )

    def test_target_owner_may_only_request_is_rejected(self):
        """A target the owner could request but does not yet hold is refused: approving it
        would mean asking a reviewer to judge a request with no justification, since no flow
        runs on this path."""
        owner = create_test_user()
        reviewer = create_test_user()
        app = self._app()
        # Bound to somebody else, so the owner does not currently pass.
        PolicyBinding.objects.create(target=app, user=create_test_user(), order=0)
        self._requestable_by(app, owner, reviewer)
        _, agent_client = self._agent_for(owner)

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(GrantRequest.objects.exists())

    def test_rule_reviewer_cannot_act_on_agent_request(self):
        """A held target can still carry a RequestRule, but its reviewers have no say in an
        agent's request -- they must not be able to deny it (a denial finalizes immediately)
        or revoke the grant, and it must not show up in their queue."""
        owner = create_test_user()
        reviewer = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        self._requestable_by(app, owner, reviewer)
        agent, agent_client = self._agent_for(owner)

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 201, res.content)
        req = GrantRequest.objects.get(pk=res.json()["grant_request"]["uuid"])

        # Not in the reviewer's queue...
        self.client.force_login(reviewer)
        res = self.client.get(reverse("authentik_api:grantrequest-pending-review"))
        self.assertEqual(res.json()["results"], [])
        # ...and they cannot deny it.
        self.assertEqual(self._fulfill(reviewer, req, status="denied").status_code, 403)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)

        # The owner approves; the reviewer still cannot revoke the resulting grant.
        self.assertEqual(self._fulfill(owner, req).status_code, 204)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.client.force_login(reviewer)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 403, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        self.assertTrue(PolicyEngine(app, agent).build().passing)

    def test_non_expiring_agent_cannot_request(self):
        """Delegated access is bounded by the agent's own lifetime, so a standing agent has
        nothing to bound the grant with and may not request at all."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)
        agent.expiring = False
        agent.expires = None
        agent.save()

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 403, res.content)
        self.assertFalse(GrantRequest.objects.exists())

    def test_owner_denial_finalizes_immediately(self):
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)

        req = GrantRequest.objects.get(
            pk=self._request_access(agent_client, app).json()["grant_request"]["uuid"]
        )
        res = self._fulfill(owner, req, status="denied")
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.DENIED)
        self.assertFalse(PolicyBinding.objects.filter(user=agent, target=app).exists())

    def test_target_owner_cannot_reach_is_rejected(self):
        """An agent can never reach past its owner: a target the owner neither has access to
        nor may request is refused outright."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=create_test_user(), order=0)
        _, agent_client = self._agent_for(owner)

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(GrantRequest.objects.exists())

    def test_one_unheld_target_rejects_the_batch(self):
        """A batch is all-or-nothing: one target the owner does not hold refuses the whole
        request, so a held target cannot smuggle an unheld one through with it."""
        owner = create_test_user()
        reviewer = create_test_user()
        held, requestable = self._app(), self._app()
        PolicyBinding.objects.create(target=held, user=owner, order=0)
        PolicyBinding.objects.create(target=requestable, user=create_test_user(), order=0)
        self._requestable_by(requestable, owner, reviewer)
        _, agent_client = self._agent_for(owner)

        res = self._request_access(agent_client, held, requestable)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(GrantRequest.objects.exists())

    def test_entitlement_owner_holds_owner_approval_suffices(self):
        """An entitlement the owner is actually bound to is genuinely held, so the owner's
        approval alone grants it -- the application case, for a child target."""
        owner = create_test_user()
        app = self._app()
        ent = self._entitlement(app)
        PolicyBinding.objects.create(target=ent, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)

        self.assertIn(ent, owner.app_entitlements(app))
        self.assertNotIn(ent, agent.app_entitlements(app))

        res = self._request_access(agent_client, ent)
        self.assertEqual(res.status_code, 201, res.content)
        req = GrantRequest.objects.get(pk=res.json()["grant_request"]["uuid"])

        self.assertEqual(self._fulfill(owner, req).status_code, 204)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)
        # Checked through authentik's own definition of holding an entitlement, not just the
        # presence of a PolicyBinding row.
        self.assertIn(ent, agent.app_entitlements(app))

    def test_unbound_entitlement_rejected(self):
        """An entitlement with no bindings is held by NOBODY -- unlike an application, where no
        bindings means everyone -- so the owner does not hold it and the agent cannot ask for
        it. True whether or not a RequestRule happens to cover it."""
        owner = create_test_user()
        reviewer = create_test_user()
        app = self._app()
        ruleless = self._entitlement(app)
        covered = self._entitlement(app)
        self._requestable_by(covered, owner, reviewer)
        _, agent_client = self._agent_for(owner)

        self.assertNotIn(ruleless, owner.app_entitlements(app))
        self.assertNotIn(covered, owner.app_entitlements(app))

        for ent in (ruleless, covered):
            res = self._request_access(agent_client, ent)
            self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(GrantRequest.objects.exists())

    def test_held_app_and_entitlement_batch(self):
        """A held application and a held entitlement in one call: the two `_owner_holds`
        engine passes combine, and both targets land on the request."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        ent = self._entitlement(self._app())
        PolicyBinding.objects.create(target=ent, user=owner, order=0)
        _, agent_client = self._agent_for(owner)

        res = self._request_access(agent_client, app, ent)
        self.assertEqual(res.status_code, 201, res.content)
        req = GrantRequest.objects.get(pk=res.json()["grant_request"]["uuid"])
        self.assertEqual(req.targets.count(), 2)

    def test_non_agent_callers_rejected(self):
        """Only an agent may use this endpoint."""
        user = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=user, order=0)

        self.client.force_login(user)
        res = self.client.post(
            reverse("authentik_api:grantrequest-agent"),
            data={"pbms": [str(app.pk)]},
            format="json",
        )
        self.assertEqual(res.status_code, 403, res.content)

        # A plain service account is not an agent either.
        service_account = User.objects.create(
            username=generate_id(), type=UserTypes.SERVICE_ACCOUNT
        )
        token = Token.objects.create(
            identifier=generate_id(),
            intent=TokenIntents.INTENT_API,
            user=service_account,
            expiring=False,
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        res = self._request_access(client, app)
        self.assertEqual(res.status_code, 403, res.content)

    def test_orphaned_agent_rejected(self):
        """Deleting the owner orphans the agent (Actor.parent is SET_DEFAULT); with nobody
        left to approve, it cannot request anything."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)

        owner.delete()
        agent.refresh_from_db()
        self.assertIsNone(agent.parent)

        res = self._request_access(agent_client, app)
        self.assertEqual(res.status_code, 403, res.content)

    def test_agent_cannot_fulfill_its_own_request(self):
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        _, agent_client = self._agent_for(owner)

        req = GrantRequest.objects.get(
            pk=self._request_access(agent_client, app).json()["grant_request"]["uuid"]
        )
        res = agent_client.patch(
            reverse("authentik_api:grantrequest-fulfill", kwargs={"pk": req.pk}),
            data={"status": "approved", "data": {}},
            format="json",
        )
        self.assertEqual(res.status_code, 403, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.CREATED)

    def test_owner_can_revoke_without_being_a_reviewer(self):
        """The owner can end their agent's grant on their own -- reviewer eligibility never
        enters into it."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)

        req = GrantRequest.objects.get(
            pk=self._request_access(agent_client, app).json()["grant_request"]["uuid"]
        )
        self._fulfill(owner, req)
        self.assertTrue(PolicyEngine(app, agent).build().passing)

        self.client.force_login(owner)
        res = self.client.delete(
            reverse("authentik_api:grantrequest-revoke", kwargs={"pk": req.pk})
        )
        self.assertEqual(res.status_code, 204, res.content)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.REVOKED)
        self.assertFalse(PolicyEngine(app, agent).build().passing)

    def test_grant_never_outlives_the_agent(self):
        """The granted duration is capped by the agent's own expiry, so a grant can't hand
        out access that survives the identity holding it."""
        owner = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        agent, agent_client = self._agent_for(owner)
        # Well inside the "hours=1" default the request would otherwise pick up.
        agent.expires = now() + timedelta(minutes=5)
        agent.save()

        req = GrantRequest.objects.get(
            pk=self._request_access(agent_client, app).json()["grant_request"]["uuid"]
        )
        self.assertLessEqual(timedelta_from_string(req.requested_expiry), timedelta(minutes=5))
        self.assertGreater(timedelta_from_string(req.requested_expiry), timedelta(minutes=4))

    def test_pending_review_surfaces_agent_request_to_owner(self):
        """An agent request reaches its owner through ownership rather than through reviewer
        eligibility, and reaches nobody else."""
        owner = create_test_user()
        outsider = create_test_user()
        app = self._app()
        PolicyBinding.objects.create(target=app, user=owner, order=0)
        _, agent_client = self._agent_for(owner)

        req = GrantRequest.objects.get(
            pk=self._request_access(agent_client, app).json()["grant_request"]["uuid"]
        )

        self.client.force_login(owner)
        res = self.client.get(reverse("authentik_api:grantrequest-pending-review"))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual({r["uuid"] for r in res.json()["results"]}, {str(req.pk)})

        self.client.force_login(outsider)
        res = self.client.get(reverse("authentik_api:grantrequest-pending-review"))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["results"], [])
