"""Test bindings API"""

from django.apps import apps
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Source
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.models import Device
from authentik.flows.models import Flow, FlowStageBinding
from authentik.policies.api.bindings import PolicyBindingModelForeignKey
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.sources.oauth.models import OAuthSource
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
            Device.objects.create(name="binding-test", identifier="binding-test"),
            OAuthSource.objects.create(name="binding-test", slug="binding-test"),
        ]

    def test_policy_binding_descendants_share_parent_pk(self):
        """Test policy binding subclasses preserve the same primary key"""
        for model in apps.get_models():
            if not issubclass(model, PolicyBindingModel):
                continue
            for parent, link in model._meta.parents.items():
                if parent is PolicyBindingModel or not issubclass(parent, PolicyBindingModel):
                    continue
                with self.subTest(model=model._meta.label, parent=parent._meta.label):
                    if model._meta.proxy:
                        self.assertIs(model._meta.pk, parent._meta.pk)
                    else:
                        self.assertIs(model._meta.pk, link)
                        self.assertIs(link.target_field, parent._meta.pk)

    def test_target_field_with_intermediate_source(self):
        """Test intermediate sources retain concrete target primary keys"""
        source = OAuthSource.objects.create(name="binding-test", slug="binding-test")
        intermediate = Source.objects.get(pk=source.pk)
        concrete = PolicyBindingModel.objects.get_subclass(pbm_uuid=source.pbm_uuid)
        self.assertIs(type(intermediate), Source)
        self.assertIs(type(concrete), OAuthSource)
        field = PolicyBindingModelForeignKey(read_only=True)
        with self.assertNumQueries(0):
            self.assertEqual(field.to_representation(intermediate), concrete.pk)

    def test_target_primary_keys(self):
        """Test concrete target primary keys in list and detail responses"""
        expected = {}
        targets = self._create_targets()
        for target in targets:
            binding = PolicyBinding.objects.create(target=target, user=self.user, order=0)
            expected[str(binding.pk)] = str(target.pk)
            response = self.client.get(
                reverse("authentik_api:policybinding-detail", kwargs={"pk": binding.pk})
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["target"], str(target.pk))

        response = self.client.get(
            reverse("authentik_api:policybinding-list"),
            {"target_in": [target.pbm_uuid for target in targets]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {binding["pk"]: binding["target"] for binding in response.json()["results"]},
            expected,
        )

    def test_target_field_without_prefetch(self):
        """Test target primary keys without prefetching"""
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
        """Test concrete target primary keys in create and update responses"""
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
        """Test list query counts remain constant as the page size increases"""
        targets = []
        for index in range(20):
            target = Application.objects.create(name=f"binding-{index}", slug=f"binding-{index}")
            PolicyBinding.objects.create(target=target, user=self.user, order=index)
            targets.append(target.pbm_uuid)

        url = reverse("authentik_api:policybinding-list")
        filters = {"target_in": targets, "policy__isnull": "true"}
        # Warm request-level caches before comparing page sizes.
        self.client.get(url, {"page_size": 1, **filters})
        with CaptureQueriesContext(connection) as single:
            response = self.client.get(url, {"page_size": 1, **filters})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        with CaptureQueriesContext(connection) as multiple:
            response = self.client.get(url, {"page_size": 20, **filters})
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
