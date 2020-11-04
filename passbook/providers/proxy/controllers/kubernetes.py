"""Proxy Provider Kubernetes Contoller"""
from passbook.outposts.controllers.kubernetes import KubernetesController
from passbook.outposts.models import KubernetesServiceConnection, Outpost
from passbook.providers.proxy.controllers.k8s.ingress import IngressReconciler


class ProxyKubernetesController(KubernetesController):
    """Proxy Provider Kubernetes Contoller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }
        self.reconcilers["ingress"] = IngressReconciler
        self.reconcile_order.append("ingress")
