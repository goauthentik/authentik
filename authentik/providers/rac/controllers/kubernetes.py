"""RAC Provider Kubernetes Controller"""

from authentik.outposts.controllers.k8s.service import ServiceReconciler
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost


class RACKubernetesController(KubernetesController):
    """RAC Provider Kubernetes Controller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = []
        del self.reconcilers[ServiceReconciler.reconciler_name()]
