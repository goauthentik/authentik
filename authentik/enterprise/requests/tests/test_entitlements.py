from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, ApplicationEntitlement
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.requests.models import (
    RequestRule,
    RequestRuleBinding,
    RequestRuleChildBinding,
)
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class ApplicationEntitlementRequestTests(APITestCase):
    def setUp(self):
        Application.objects.all().delete()
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.entitlement = ApplicationEntitlement.objects.create(
            name=generate_id(),
            app=self.app,
        )

    def test_requestable_none(self):
        user = create_test_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:applicationentitlement-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 0)
        self.assertEqual(len(content["results"]), 0)

    def test_requestable_direct_no_access(self):
        """A RequestRuleBinding targeting the entitlement directly, but the requesting
        user isn't among its reviewers/passers."""
        other_user = create_test_user()

        user = create_test_user()
        self.client.force_login(user)

        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=self.entitlement)
        PolicyBinding.objects.create(target=rule_binding, user=other_user, order=0)

        res = self.client.get(reverse("authentik_api:applicationentitlement-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 0)
        self.assertEqual(len(content["results"]), 0)

    def test_requestable_direct_access(self):
        """A RequestRuleBinding targeting the entitlement directly."""
        user = create_test_user()
        self.client.force_login(user)

        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=self.entitlement)
        PolicyBinding.objects.create(target=rule_binding, user=user, order=0)

        res = self.client.get(reverse("authentik_api:applicationentitlement-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(len(content["results"]), 1)
        self.assertEqual(content["results"][0]["pbm_uuid"], str(self.entitlement.pbm_uuid))
        self.assertEqual(content["results"][0]["parent"]["slug"], self.app.slug)

    def test_requestable_via_parent_child_binding_no_access(self):
        """A RequestRuleBinding targeting the parent Application, with the entitlement
        listed as a related child binding, but the requesting user isn't eligible."""
        other_user = create_test_user()

        user = create_test_user()
        self.client.force_login(user)

        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=self.app)
        RequestRuleChildBinding.objects.create(binding=rule_binding, target=self.entitlement)
        PolicyBinding.objects.create(target=rule_binding, user=other_user, order=0)

        res = self.client.get(reverse("authentik_api:applicationentitlement-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 0)
        self.assertEqual(len(content["results"]), 0)

    def test_requestable_via_parent_child_binding_access(self):
        """A RequestRuleBinding targeting the parent Application, with the entitlement
        listed as a related child binding, should make the entitlement itself
        individually requestable -- even though no RequestRuleBinding targets it
        directly."""
        user = create_test_user()
        self.client.force_login(user)

        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=self.app)
        RequestRuleChildBinding.objects.create(binding=rule_binding, target=self.entitlement)
        PolicyBinding.objects.create(target=rule_binding, user=user, order=0)

        res = self.client.get(reverse("authentik_api:applicationentitlement-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(len(content["results"]), 1)
        self.assertEqual(content["results"][0]["pbm_uuid"], str(self.entitlement.pbm_uuid))
        self.assertEqual(content["results"][0]["parent"]["slug"], self.app.slug)

    def test_requestable_filtered_by_app(self):
        """The `app` query param (respected via filter_queryset) should scope results
        to entitlements belonging to that application only."""
        other_app = Application.objects.create(name=generate_id(), slug=generate_id())
        other_entitlement = ApplicationEntitlement.objects.create(name=generate_id(), app=other_app)

        user = create_test_user()
        self.client.force_login(user)

        rule = RequestRule.objects.create(name=generate_id())
        for entitlement in (self.entitlement, other_entitlement):
            rule_binding = RequestRuleBinding.objects.create(rule=rule, target=entitlement)
            PolicyBinding.objects.create(target=rule_binding, user=user, order=0)

        res = self.client.get(
            reverse("authentik_api:applicationentitlement-requestable"), {"app": self.app.pk}
        )
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["pbm_uuid"], str(self.entitlement.pbm_uuid))
