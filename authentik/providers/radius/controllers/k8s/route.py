from dataclasses import dataclass

from kubernetes.client import V1ObjectMeta

from authentik.outposts.controllers.k8s.route import (
    Route,
    RouteBackendRef,
    RouteReconciler,
    RouteSpec,
)
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.kubernetes import KubernetesController


@dataclass(slots=True)
class UDPRouteSpecRule:
    backendRefs: list[RouteBackendRef]


@dataclass(slots=True)
class UDPRouteSpec(RouteSpec):
    rules: list[UDPRouteSpecRule]


@dataclass(slots=True)
class UDPRoute(Route):
    kind: str
    metadata: V1ObjectMeta
    spec: UDPRouteSpec


class UDPRouteReconciler(RouteReconciler):
    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.crd_plural = "udproutes"
        self.crd_version = "v1alpha2"
        self.spec_type = UDPRoute

    @staticmethod
    def reconciler_name() -> str:
        return "udproute"

    def reconcile(self, current: UDPRoute, reference: UDPRoute):
        super().reconcile(current, reference)
        if current.spec.rules != reference.spec.rules:
            raise NeedsUpdate()

    def get_reference_object(self) -> UDPRoute:
        return UDPRoute(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="UDPRoute",
            metadata=self.get_object_meta(),
            spec=UDPRouteSpec(
                **self.get_reference_object_spec_base(),
                rules=[
                    UDPRouteSpecRule(
                        backendRefs=[RouteBackendRef(name=self.name, port=1812)],
                    )
                ],
            ),
        )
