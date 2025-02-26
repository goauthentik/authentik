from dataclasses import dataclass
from urllib.parse import urlparse

from kubernetes.client import V1ObjectMeta

from authentik.outposts.controllers.k8s.route import (
    Route,
    RouteBackendRef,
    RouteReconciler,
    RouteSpec,
)
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.providers.proxy.models import ProxyMode, ProxyProvider


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
class HTTPRouteSpec(RouteSpec):
    hostnames: list[str]
    rules: list[HTTPRouteSpecRule]


@dataclass(slots=True)
class HTTPRoute(Route):
    kind: str
    metadata: V1ObjectMeta
    spec: HTTPRouteSpec


class HTTPRouteReconciler(RouteReconciler):
    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.crd_plural = "httproutes"
        self.spec_type = HTTPRoute

    @staticmethod
    def reconciler_name() -> str:
        return "httproute"

    def reconcile(self, current: HTTPRoute, reference: HTTPRoute):
        super().reconcile(current, reference)
        if current.spec.hostnames != reference.spec.hostnames:
            raise NeedsUpdate()
        if current.spec.rules != reference.spec.rules:
            raise NeedsUpdate()

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
                **self.get_reference_object_spec_base(),
                hostnames=hostnames,
                rules=rules,
            ),
        )
