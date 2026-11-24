from dataclasses import dataclass
from urllib.parse import urlparse

from dacite.core import from_dict

from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.providers.proxy.controllers.k8s.httproute import (
    HTTPRouteMetadata,
    HTTPRouteReconciler,
)
from authentik.providers.proxy.models import ProxyProvider


@dataclass(slots=True)
class ListenerSetParentRef:
    name: str
    namespace: str | None = None
    kind: str = "Gateway"
    group: str = "gateway.networking.k8s.io"


@dataclass(slots=True)
class ListenerCertificateRef:
    name: str
    kind: str = "Secret"
    group: str = ""


@dataclass(slots=True)
class ListenerTLS:
    certificateRefs: list[ListenerCertificateRef]
    mode: str = "Terminate"


@dataclass(slots=True)
class Listener:
    name: str
    hostname: str
    port: int
    protocol: str
    tls: ListenerTLS | None = None


@dataclass(slots=True)
class ListenerSetSpec:
    parentRef: ListenerSetParentRef
    listeners: list[Listener]


@dataclass(slots=True)
class ListenerSet:
    apiVersion: str
    kind: str
    metadata: HTTPRouteMetadata
    spec: ListenerSetSpec


class ListenerSetReconciler(HTTPRouteReconciler):
    """Kubernetes Gateway API ListenerSet Reconciler"""

    def __init__(self, controller: KubernetesController) -> None:
        super().__init__(controller)
        self.crd_plural = "listenersets"

    @staticmethod
    def reconciler_name() -> str:
        return "listenerset"

    @property
    def noop(self) -> bool:
        if not self.controller.outpost.config.kubernetes_listenerset_parent_ref:
            self.logger.debug("ListenerSet parentRef not set.")
            return True
        if not self.crd_exists():
            self.logger.debug("CRD doesn't exist")
            return True
        return False

    def reconcile(self, current: ListenerSet, reference: ListenerSet):
        if current.metadata.labels != reference.metadata.labels:
            raise NeedsUpdate()
        if current.spec != reference.spec:
            raise NeedsUpdate()

    def get_reference_object(self) -> ListenerSet:
        secret_name = self.controller.outpost.config.kubernetes_ingress_secret_name
        hostnames = sorted(
            {
                urlparse(provider.external_host).hostname
                for provider in ProxyProvider.objects.filter(outpost__in=[self.controller.outpost])
            }
        )
        # Listeners can be adjusted with `kubernetes_json_patches`, e.g. for a non-standard port
        listeners = [
            (
                Listener(
                    name=hostname,
                    hostname=hostname,
                    port=443,
                    protocol="HTTPS",
                    tls=ListenerTLS(certificateRefs=[ListenerCertificateRef(name=secret_name)]),
                )
                if secret_name
                else Listener(name=hostname, hostname=hostname, port=80, protocol="HTTP")
            )
            for hostname in hostnames
        ]
        return ListenerSet(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="ListenerSet",
            metadata=HTTPRouteMetadata(
                name=self.name,
                namespace=self.namespace,
                labels=self.get_object_meta().labels,
            ),
            spec=ListenerSetSpec(
                parentRef=from_dict(
                    ListenerSetParentRef,
                    self.controller.outpost.config.kubernetes_listenerset_parent_ref,
                ),
                listeners=listeners,
            ),
        )

    def retrieve(self) -> ListenerSet:
        return from_dict(
            ListenerSet,
            self.api.get_namespaced_custom_object(
                group=self.crd_group,
                version=self.crd_version,
                plural=self.crd_plural,
                namespace=self.namespace,
                name=self.name,
            ),
        )
