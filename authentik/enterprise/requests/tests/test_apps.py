from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.requests.models import RequestRule, RequestRuleBinding
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class AppRequestTests(APITestCase):
    def setUp(self):
        Application.objects.all().delete()

    def test_requestable_none(self):
        user = create_test_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:application-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 0)
        self.assertEqual(len(content["results"]), 0)

    def test_requestable_no_policy(self):
        user = create_test_user()
        self.client.force_login(user)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        RequestRuleBinding.objects.create(rule=rule, target=app)

        res = self.client.get(reverse("authentik_api:application-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(len(content["results"]), 1)
        self.assertEqual(content["results"][0]["slug"], app.slug)

    def test_requestable_no_access(self):
        other_user = create_test_user()

        user = create_test_user()
        self.client.force_login(user)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=other_user, order=0)

        res = self.client.get(reverse("authentik_api:application-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 0)
        self.assertEqual(len(content["results"]), 0)

    def test_requestable_access(self):
        user = create_test_user()
        self.client.force_login(user)

        app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        rule = RequestRule.objects.create(name=generate_id())
        rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
        PolicyBinding.objects.create(target=rule_binding, user=user, order=0)

        res = self.client.get(reverse("authentik_api:application-requestable"))
        content = loads(res.content.decode())
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(len(content["results"]), 1)
        self.assertEqual(content["results"][0]["slug"], app.slug)
