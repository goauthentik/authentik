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
class TCPRouteSpecRule:
    backendRefs: list[RouteBackendRef]


@dataclass(slots=True)
class TCPRouteSpec(RouteSpec):
    rules: list[TCPRouteSpecRule]


@dataclass(slots=True)
class TCPRoute(Route):
    kind: str
    metadata: V1ObjectMeta
    spec: TCPRouteSpec


class TCPRouteReconciler(RouteReconciler):
    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.crd_plural = "tcproutes"
        self.crd_version = "v1alpha2"
        self.spec_type = TCPRoute

    @staticmethod
    def reconciler_name() -> str:
        return "tcproute"

    def reconcile(self, current: TCPRoute, reference: TCPRoute):
        super().reconcile(current, reference)
        if current.spec.rules != reference.spec.rules:
            raise NeedsUpdate()

    def get_reference_object(self) -> TCPRoute:
        return TCPRoute(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="TCPRoute",
            metadata=self.get_object_meta(),
            spec=TCPRouteSpec(
                **self.get_reference_object_spec_base(),
                rules=[
                    TCPRouteSpecRule(
                        backendRefs=[RouteBackendRef(name=self.name, port=389)],
                    )
                ],
            ),
        )
