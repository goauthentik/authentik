"""Kubernetes controller tests"""

from django.test import TestCase

from authentik.blueprints.tests import reconcile_app
from authentik.lib.generators import generate_id
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.controllers.k8s.deployment import DeploymentReconciler
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType


class KubernetesControllerTests(TestCase):
    """Kubernetes controller tests"""

    @reconcile_app("authentik_outposts")
    def setUp(self) -> None:
        self.outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
        )
        self.integration = KubernetesServiceConnection(name="test")

    def test_gen_name(self):
        """Ensure the generated name is valid"""
        controller = KubernetesController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(),
            self.integration,
            # Pass something not-none as client so we don't
            # attempt to connect to K8s as that's not needed
            client=self,
        )
        rec = DeploymentReconciler(controller)
        self.assertEqual(rec.name, "ak-outpost-authentik-embedded-outpost")

        controller.outpost.name = generate_id()
        self.assertLess(len(rec.name), 64)

        # Test custom naming template
        _cfg = controller.outpost.config
        _cfg.object_naming_template = ""
        controller.outpost.config = _cfg
        self.assertEqual(rec.name, f"outpost-{controller.outpost.uuid.hex}")
        self.assertLess(len(rec.name), 64)
