"""Test bindings API"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding
from authentik.policies.api.bindings import PolicyBindingModelForeignKey
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.stages.dummy.models import DummyStage


class TestBindingsAPI(APITestCase):
    """Test bindings API"""

    def setUp(self) -> None:
        super().setUp()
        self.pbm = PolicyBindingModel.objects.create()
        self.user = create_test_admin_user()
        self.group = self.user.groups.first()
        self.client.force_login(self.user)

    def _create_targets(self) -> list[PolicyBindingModel]:
        """Include targets whose concrete and base primary keys differ."""
        flow = Flow.objects.create(name="binding-test", slug="binding-test")
        stage = DummyStage.objects.create(name="binding-test")
        stage_binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=0)
        self.assertNotEqual(flow.pk, flow.pbm_uuid)
        self.assertNotEqual(stage_binding.pk, stage_binding.pbm_uuid)
        return [
            self.pbm,
            Application.objects.create(name="binding-test", slug="binding-test"),
            flow,
            stage_binding,
        ]

    def test_target_primary_keys(self):
        """List and detail responses expose concrete target primary keys."""
        expected = {}
        for target in self._create_targets():
            binding = PolicyBinding.objects.create(target=target, user=self.user, order=0)
            expected[str(binding.pk)] = str(target.pk)
            response = self.client.get(
                reverse("authentik_api:policybinding-detail", kwargs={"pk": binding.pk})
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["target"], str(target.pk))

        response = self.client.get(reverse("authentik_api:policybinding-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {binding["pk"]: binding["target"] for binding in response.json()["results"]},
            expected,
        )

    def test_target_field_without_prefetch(self):
        """Keep resolving base objects supplied by other serializer callers."""
        field = PolicyBindingModelForeignKey(read_only=True)
        for target in self._create_targets():
            with self.subTest(target=type(target).__name__):
                base = PolicyBindingModel.objects.get(pk=target.pbm_uuid)
                with self.assertNumQueries(1):
                    self.assertEqual(field.to_representation(base), target.pk)
                if type(target) is not PolicyBindingModel:
                    with self.assertNumQueries(0):
                        self.assertEqual(field.to_representation(target), target.pk)

    def test_target_primary_keys_on_write(self):
        """Create/update responses retain subclass IDs without relying on prefetch."""
        for target in self._create_targets():
            with self.subTest(target=type(target).__name__):
                response = self.client.post(
                    reverse("authentik_api:policybinding-list"),
                    data={"target": target.pbm_uuid, "user": self.user.pk, "order": 0},
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["target"], str(target.pk))
                response = self.client.put(
                    reverse(
                        "authentik_api:policybinding-detail", kwargs={"pk": response.json()["pk"]}
                    ),
                    data={"target": target.pbm_uuid, "user": self.user.pk, "order": 1},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["target"], str(target.pk))

    def test_list_query_count(self):
        """Resolving targets must not add a query for every binding on the page."""
        for index in range(20):
            target = Application.objects.create(name=f"binding-{index}", slug=f"binding-{index}")
            PolicyBinding.objects.create(target=target, user=self.user, order=index)

        url = reverse("authentik_api:policybinding-list")
        # Warm request-level caches before comparing page sizes.
        self.client.get(url, {"page_size": 1, "policy__isnull": "true"})
        with CaptureQueriesContext(connection) as single:
            response = self.client.get(url, {"page_size": 1, "policy__isnull": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        with CaptureQueriesContext(connection) as multiple:
            response = self.client.get(url, {"page_size": 20, "policy__isnull": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 20)
        self.assertEqual(len(single), len(multiple))

    def test_valid_binding(self):
        """Test valid binding"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={
                "target": self.pbm.pk,
                "user": self.user.pk,
                "order": 0,
                "dry_run": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["dry_run"])
        self.assertTrue(PolicyBinding.objects.get(pk=response.json()["pk"]).dry_run)

    def test_invalid_too_much(self):
        """Test invalid binding (too much)"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={
                "target": self.pbm.pk,
                "user": self.user.pk,
                "group": self.group.pk,
                "order": 0,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["Only one of 'group', 'policy', 'user' can be set."]},
        )

    def test_invalid_too_little(self):
        """Test invalid binding (too little)"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={"target": self.pbm.pk, "order": 0},
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["One of 'group', 'policy', 'user' must be set."]},
        )
