"""Kubernetes Traefik Middleware Reconciler"""
from typing import TYPE_CHECKING

from authentik.providers.proxy.controllers.k8s.traefik_3 import Traefik3MiddlewareReconciler

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class Traefik2MiddlewareReconciler(Traefik3MiddlewareReconciler):
    """Kubernetes Traefik Middleware Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.crd_name = "middlewares.traefik.containo.us"
        self.crd_group = "traefik.containo.us"
        self.crd_version = "v1alpha1"
        self.crd_plural = "middlewares"
