from typing import TYPE_CHECKING
from urllib.parse import urlparse

from kubernetes.client import ApiextensionsV1Api, CustomObjectsApi, V1ObjectMeta
from pydantic import BaseModel, Field

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class RouteBackendRef(BaseModel):
    name: str
    port: int


class RouteSpecParentRefs(BaseModel):
    name: str
    sectionName: str | None = None
    port: int | None = None
    namespace: str | None = None
    kind: str = "Gateway"
    group: str = "gateway.networking.k8s.io"


class HTTPRouteSpecRuleMatchPath(BaseModel):
    type: str
    value: str


class HTTPRouteSpecRuleMatchHeader(BaseModel):
    name: str
    value: str
    type: str = "Exact"


class HTTPRouteSpecRuleMatch(BaseModel):
    path: HTTPRouteSpecRuleMatchPath
    headers: list[HTTPRouteSpecRuleMatchHeader]


class HTTPRouteSpecRule(BaseModel):
    backendRefs: list[RouteBackendRef]
    matches: list[HTTPRouteSpecRuleMatch]


class HTTPRouteSpec(BaseModel):
    parentRefs: list[RouteSpecParentRefs]
    hostnames: list[str]
    rules: list[HTTPRouteSpecRule]


class HTTPRouteMetadata(BaseModel):
    name: str
    namespace: str
    annotations: dict = Field(default_factory=dict)
    labels: dict = Field(default_factory=dict)


class HTTPRoute(BaseModel):
    apiVersion: str
    kind: str
    metadata: HTTPRouteMetadata
    spec: HTTPRouteSpec


class HTTPRouteReconciler(KubernetesObjectReconciler):
    """Kubernetes Gateway API HTTPRoute Reconciler"""

    def __init__(self, controller: KubernetesController) -> None:
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
                                HTTPRouteSpecRuleMatchHeader(
                                    name="Host",
                                    value=external_host_name.hostname,
                                )
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
                                HTTPRouteSpecRuleMatchHeader(
                                    name="Host",
                                    value=external_host_name.hostname,
                                )
                            ],
                            path=HTTPRouteSpecRuleMatchPath(type="PathPrefix", value="/"),
                        )
                    ],
                )
            hostnames.append(external_host_name.hostname)
            rules.append(rule)

        return HTTPRoute(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="HTTPRoute",
            metadata=HTTPRouteMetadata(
                name=self.name,
                namespace=self.namespace,
                annotations=self.controller.outpost.config.kubernetes_httproute_annotations,
                labels=self.get_object_meta().labels,
            ),
            spec=HTTPRouteSpec(
                parentRefs=[
                    RouteSpecParentRefs.model_validate(spec)
                    for spec in self.controller.outpost.config.kubernetes_httproute_parent_refs
                ],
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
            body=reference.model_dump(mode="json"),
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
        return HTTPRoute.model_validate(
            self.api.get_namespaced_custom_object(
                group=self.crd_group,
                version=self.crd_version,
                plural=self.crd_plural,
                namespace=self.namespace,
                name=self.name,
            )
        )

    def update(self, current: HTTPRoute, reference: HTTPRoute):
        return self.api.patch_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
            body=reference.model_dump(mode="json"),
            field_manager=FIELD_MANAGER,
        )
