from json import loads

from django.db import connections
from django.test.utils import CaptureQueriesContext
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

    def test_requestable_query_count_independent_of_app_count(self):
        """Every candidate must be resolved in a single policy pass -- the endpoint must
        not build one ListPolicyEngine per application."""
        user = create_test_user()
        self.client.force_login(user)
        rule = RequestRule.objects.create(name=generate_id())

        def add_apps(count: int):
            for _ in range(count):
                app = Application.objects.create(name=generate_id(), slug=generate_id())
                rule_binding = RequestRuleBinding.objects.create(rule=rule, target=app)
                PolicyBinding.objects.create(target=rule_binding, user=user, order=0)

        url = reverse("authentik_api:application-requestable")

        add_apps(5)
        self.client.get(url)  # warm any per-process/session caches
        with CaptureQueriesContext(connections["default"]) as ctx_small:
            res = self.client.get(url)
        self.assertEqual(loads(res.content.decode())["pagination"]["count"], 5)
        baseline = len(ctx_small.captured_queries)

        add_apps(25)
        self.client.get(url)
        with CaptureQueriesContext(connections["default"]) as ctx_large:
            res = self.client.get(url)
        self.assertEqual(loads(res.content.decode())["pagination"]["count"], 30)

        self.assertLessEqual(
            len(ctx_large.captured_queries),
            baseline + 2,
            (
                f"Query count grew from {baseline} to {len(ctx_large.captured_queries)} "
                "after adding 25 applications -- access is being evaluated per object."
            ),
        )

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
