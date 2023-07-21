"""Kubernetes Traefik Middleware Reconciler"""
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.providers.proxy.controllers.k8s.traefik_2 import Traefik2MiddlewareReconciler
from authentik.providers.proxy.controllers.k8s.traefik_3 import (
    Traefik3MiddlewareReconciler,
    TraefikMiddleware,
)


class TraefikMiddlewareReconciler(KubernetesObjectReconciler):
    """Kubernetes Traefik Middleware Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.reconciler = Traefik3MiddlewareReconciler(controller)
        if not self.reconciler.crd_exists():
            self.reconciler = Traefik2MiddlewareReconciler(controller)

    @staticmethod
    def reconciler_name() -> str:
        return "traefik middleware"

    @property
    def noop(self) -> bool:
        return self.reconciler.noop

    def reconcile(self, current: TraefikMiddleware, reference: TraefikMiddleware):
        return self.reconcile(current, reference)

    def get_reference_object(self) -> TraefikMiddleware:
        return self.get_reference_object()

    def create(self, reference: TraefikMiddleware):
        return self.create(reference)

    def delete(self, reference: TraefikMiddleware):
        return self.delete(reference)

    def retrieve(self) -> TraefikMiddleware:
        return self.retrieve()

    def update(self, current: TraefikMiddleware, reference: TraefikMiddleware):
        return self.update(current, reference)
