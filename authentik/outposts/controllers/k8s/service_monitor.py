"""Kubernetes Prometheus ServiceMonitor Reconciler"""

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from dacite.core import from_dict
from kubernetes.client import ApiextensionsV1Api, CustomObjectsApi

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


@dataclass(slots=True)
class PrometheusServiceMonitorSpecEndpoint:
    """Prometheus ServiceMonitor endpoint spec"""

    port: str
    path: str = field(default="/metrics")


@dataclass(slots=True)
class PrometheusServiceMonitorSpecSelector:
    """Prometheus ServiceMonitor selector spec"""

    matchLabels: dict


@dataclass(slots=True)
class PrometheusServiceMonitorSpec:
    """Prometheus ServiceMonitor spec"""

    endpoints: list[PrometheusServiceMonitorSpecEndpoint]

    selector: PrometheusServiceMonitorSpecSelector


@dataclass(slots=True)
class PrometheusServiceMonitorMetadata:
    """Prometheus ServiceMonitor metadata"""

    name: str
    namespace: str
    labels: dict = field(default_factory=dict)


@dataclass(slots=True)
class PrometheusServiceMonitor:
    """Prometheus ServiceMonitor"""

    apiVersion: str
    kind: str
    metadata: PrometheusServiceMonitorMetadata
    spec: PrometheusServiceMonitorSpec


CRD_NAME = "servicemonitors.monitoring.coreos.com"
CRD_GROUP = "monitoring.coreos.com"
CRD_VERSION = "v1"
CRD_PLURAL = "servicemonitors"


class PrometheusServiceMonitorReconciler(KubernetesObjectReconciler[PrometheusServiceMonitor]):
    """Kubernetes Prometheus ServiceMonitor Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api_ex = ApiextensionsV1Api(controller.client)
        self.api = CustomObjectsApi(controller.client)

    @staticmethod
    def reconciler_name() -> str:
        return "prometheus servicemonitor"

    @property
    def noop(self) -> bool:
        if not self._crd_exists():
            self.logger.debug("CRD doesn't exist")
            return True
        return self.is_embedded

    def _crd_exists(self) -> bool:
        """Check if the Prometheus ServiceMonitor exists"""
        return bool(
            len(
                self.api_ex.list_custom_resource_definition(
                    field_selector=f"metadata.name={CRD_NAME}"
                ).items
            )
        )

    def get_reference_object(self) -> PrometheusServiceMonitor:
        """Get service monitor object for outpost"""
        return PrometheusServiceMonitor(
            apiVersion=f"{CRD_GROUP}/{CRD_VERSION}",
            kind="ServiceMonitor",
            metadata=PrometheusServiceMonitorMetadata(
                name=self.name,
                namespace=self.namespace,
                labels=self.get_object_meta().labels,
            ),
            spec=PrometheusServiceMonitorSpec(
                endpoints=[
                    PrometheusServiceMonitorSpecEndpoint(
                        port="http-metrics",
                    )
                ],
                selector=PrometheusServiceMonitorSpecSelector(
                    matchLabels=self.get_object_meta(name=self.name).labels,
                ),
            ),
        )

    def create(self, reference: PrometheusServiceMonitor):
        return self.api.create_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            plural=CRD_PLURAL,
            namespace=self.namespace,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )

    def delete(self, reference: PrometheusServiceMonitor):
        return self.api.delete_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=self.namespace,
            plural=CRD_PLURAL,
            name=self.name,
        )

    def retrieve(self) -> PrometheusServiceMonitor:
        return from_dict(
            PrometheusServiceMonitor,
            self.api.get_namespaced_custom_object(
                group=CRD_GROUP,
                version=CRD_VERSION,
                namespace=self.namespace,
                plural=CRD_PLURAL,
                name=self.name,
            ),
        )

    def update(self, current: PrometheusServiceMonitor, reference: PrometheusServiceMonitor):
        return self.api.patch_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=self.namespace,
            plural=CRD_PLURAL,
            name=self.name,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )
