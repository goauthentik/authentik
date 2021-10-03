"""Proxy Provider Kubernetes Controller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost
from authentik.providers.proxy.controllers.k8s.ingress import IngressReconciler
from authentik.providers.proxy.controllers.k8s.traefik import TraefikMiddlewareReconciler


class ProxyKubernetesController(KubernetesController):
    """Proxy Provider Kubernetes Controller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(9000, "http", "tcp"),
            DeploymentPort(9300, "http-metrics", "tcp"),
            DeploymentPort(9443, "https", "tcp"),
        ]
        self.reconcilers["ingress"] = IngressReconciler
        self.reconcilers["traefik middleware"] = TraefikMiddlewareReconciler
        self.reconcile_order.append("ingress")
        self.reconcile_order.append("traefik middleware")
