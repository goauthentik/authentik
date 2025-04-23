from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from dacite.core import from_dict
from kubernetes.client import ApiextensionsV1Api, CustomObjectsApi, V1ObjectMeta

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

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
class HTTPRouteSpecRuleMatchPath:
    type: str
    value: str


@dataclass(slots=True)
class HTTPRouteSpecRuleMatchHeader:
    name: str
    value: str
    type: str = "Exact"


@dataclass(slots=True)
class HTTPRouteSpecRuleMatch:
    path: HTTPRouteSpecRuleMatchPath
    headers: list[HTTPRouteSpecRuleMatchHeader]


@dataclass(slots=True)
class HTTPRouteSpecRule:
    backendRefs: list[RouteBackendRef]
    matches: list[HTTPRouteSpecRuleMatch]


@dataclass(slots=True)
class HTTPRouteSpec:
    parentRefs: list[RouteSpecParentRefs]
    hostnames: list[str]
    rules: list[HTTPRouteSpecRule]


@dataclass(slots=True)
class HTTPRoute:
    apiVersion: str
    kind: str
    metadata: V1ObjectMeta
    spec: HTTPRouteSpec


class HTTPRouteReconciler(KubernetesObjectReconciler):
    """Kubernetes Gateway API HTTPRoute Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api_ex = ApiextensionsV1Api(controller.client)
        self.api = CustomObjectsApi(controller.client)
        self.crd_group = "gateway.networking.k8s.io"
        self.crd_version = "v1"
        self.crd_plural = "httproutes"

    @staticmethod
    def reconciler_name() -> str:
        return "httproute"

    @property
    def noop(self) -> bool:
        if not self.crd_exists():
            self.logger.debug("CRD doesn't exist")
            return True
        if not self.controller.outpost.config.kubernetes_httproute_parent_refs:
            self.logger.debug("HTTPRoute parentRefs not set.")
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

    def reconcile(self, current: HTTPRoute, reference: HTTPRoute):
        super().reconcile(current, reference)
        if current.metadata.annotations != reference.metadata.annotations:
            raise NeedsUpdate()
        if current.spec.parentRefs != reference.spec.parentRefs:
            raise NeedsUpdate()
        if current.spec.hostnames != reference.spec.hostnames:
            raise NeedsUpdate()
        if current.spec.rules != reference.spec.rules:
            raise NeedsUpdate()

    def get_object_meta(self, **kwargs) -> V1ObjectMeta:
        return super().get_object_meta(
            name=self.name,
            annotations=self.controller.outpost.config.kubernetes_httproute_annotations,
            **kwargs,
        )

    def get_reference_object(self) -> HTTPRoute:
        hostnames = []
        rules = []

        for proxy_provider in ProxyProvider.objects.filter(outpost__in=[self.controller.outpost]):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            if proxy_provider.mode in [ProxyMode.FORWARD_SINGLE, ProxyMode.FORWARD_DOMAIN]:
                rule = HTTPRouteSpecRule(
                    backendRefs=[RouteBackendRef(name=self.name, port=9000)],
                    matches=[
                        HTTPRouteSpecRuleMatch(
                            headers=[
                                HTTPRouteSpecRuleMatchHeader(name="Host", value=external_host_name)
                            ],
                            path=HTTPRouteSpecRuleMatchPath(
                                type="PathPrefix", value="/outpost.goauthentik.io"
                            ),
                        )
                    ],
                )
            else:
                rule = HTTPRouteSpecRule(
                    backendRefs=[RouteBackendRef(name=self.name, port=9000)],
                    matches=[
                        HTTPRouteSpecRuleMatch(
                            headers=[
                                HTTPRouteSpecRuleMatchHeader(name="Host", value=external_host_name)
                            ],
                            path=HTTPRouteSpecRuleMatchPath(type="PathPrefix", value="/"),
                        )
                    ],
                )
            hostnames.append(external_host_name)
            rules.append(rule)

        return HTTPRoute(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="HTTPRoute",
            metadata=self.get_object_meta(),
            spec=HTTPRouteSpec(
                parentRefs=self.controller.outpost.config.kubernetes_httproute_parent_refs,
                hostnames=hostnames,
                rules=rules,
            ),
        )

    def create(self, reference: HTTPRoute):
        return self.api.create_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )

    def delete(self, reference: HTTPRoute):
        return self.api.delete_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
        )

    def retrieve(self) -> HTTPRoute:
        return from_dict(
            HTTPRoute,
            self.api.get_namespaced_custom_object(
                group=self.crd_group,
                version=self.crd_version,
                plural=self.crd_plural,
                namespace=self.namespace,
                name=self.name,
            ),
        )

    def update(self, current: HTTPRoute, reference: HTTPRoute):
        return self.api.patch_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )
