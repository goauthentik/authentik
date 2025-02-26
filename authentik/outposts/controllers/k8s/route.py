from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from dacite.core import from_dict
from kubernetes.client import ApiextensionsV1Api, CustomObjectsApi, V1ObjectMeta

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


@dataclass(slots=True)
class RouteBackendRef:
    name: str
    port: int


@dataclass(slots=True)
class RouteSpecParentRefs:
    name: str
    sectionName: str | None = None
    port: int | None = None
    namespace: str | None = None
    kind: str = "Gateway"
    group: str = "gateway.networking.k8s.io"


@dataclass(slots=True)
class RouteSpec:
    parentRefs: list[RouteSpecParentRefs]


@dataclass(slots=True)
class Route:
    apiVersion: str
    kind: str
    metadata: V1ObjectMeta
    spec: RouteSpec


class RouteReconciler(KubernetesObjectReconciler):
    """Kubernetes Gateway API Route Reconciler"""

    crd_plural: str
    spec_type: type[Route]

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api_ex = ApiextensionsV1Api(controller.client)
        self.api = CustomObjectsApi(controller.client)
        self.crd_group = "gateway.networking.k8s.io"
        self.crd_version = "v1"

    @property
    def noop(self) -> bool:
        if not self.crd_exists():
            self.logger.debug("CRD doesn't exist")
            return True
        return False

    def crd_exists(self) -> bool:
        """Check if the Gateway API resources exists"""
        return bool(
            len(
                self.api_ex.list_custom_resource_definition(
                    field_selector=f"metadata.name={self.crd_plural}.{self.crd_group}"
                ).items
            )
        )

    def reconcile(self, current: Route, reference: Route):
        super().reconcile(current, reference)
        if current.metadata.annotations != reference.metadata.annotations:
            raise NeedsUpdate()
        if current.spec.parentRefs != reference.spec.parentRefs:
            raise NeedsUpdate()

    def get_object_meta(self, **kwargs) -> V1ObjectMeta:
        return super().get_object_meta(
            name=self.name,
            annotations=self.controller.outpost.config.kubernetes_route_annotations,
            **kwargs,
        )

    def get_reference_object_spec_base(self) -> dict:
        return asdict(
            RouteSpec(
                parentRefs=self.controller.outpost.config.kubernetes_route_parent_refs,
            )
        )

    def create(self, reference: Route):
        return self.api.create_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )

    def delete(self, reference: Route):
        return self.api.delete_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
        )

    def retrieve(self) -> Route:
        return from_dict(
            self.spec_type,
            self.api.get_namespaced_custom_object(
                group=self.crd_group,
                version=self.crd_version,
                plural=self.crd_plural,
                namespace=self.namespace,
                name=self.name,
            ),
        )

    def update(self, current: Route, reference: Route):
        return self.api.patch_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )
