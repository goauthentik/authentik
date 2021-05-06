"""Proxy Provider Kubernetes Contoller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost
from authentik.providers.proxy.controllers.k8s.ingress import IngressReconciler
from authentik.providers.proxy.controllers.k8s.traefik import (
    TraefikMiddlewareReconciler,
)


class ProxyKubernetesController(KubernetesController):
    """Proxy Provider Kubernetes Contoller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(4180, "http", "tcp"),
            DeploymentPort(4443, "https", "tcp"),
        ]
        self.reconcilers["ingress"] = IngressReconciler
        self.reconcilers["traefik_middleware"] = TraefikMiddlewareReconciler
        self.reconcile_order.append("ingress")
        self.reconcile_order.append("traefik_middleware")
