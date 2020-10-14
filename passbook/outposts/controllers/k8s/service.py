"""Kubernetes Service Reconciler"""
from typing import Dict

from kubernetes.client import CoreV1Api, V1Service, V1ServicePort, V1ServiceSpec

from passbook.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsUpdate,
)
from passbook.outposts.models import Outpost


class ServiceReconciler(KubernetesObjectReconciler[V1Service]):
    """Kubernetes Service Reconciler"""

    deployment_ports: Dict[str, int]

    def __init__(self, outpost: Outpost) -> None:
        super().__init__(outpost)
        self.api = CoreV1Api()
        self.deployment_ports = {}

    def reconcile(self, current: V1Service, reference: V1Service):
        if len(current.spec.ports) != len(reference.spec.ports):
            raise NeedsUpdate()
        for port in reference.spec.ports:
            if port not in current.spec.ports:
                raise NeedsUpdate()

    def get_reference_object(self) -> V1Service:
        """Get deployment object for outpost"""
        meta = self.get_object_meta(name=f"passbook-outpost-{self.outpost.name}")
        ports = []
        for port_name, port in self.deployment_ports.items():
            ports.append(V1ServicePort(name=port_name, port=port))
        return V1Service(
            metadata=meta,
            spec=V1ServiceSpec(ports=ports, selector=meta.labels, type="ClusterIP"),
        )

    def create(self, reference: V1Service):
        return self.api.create_namespaced_service(self.namespace, reference)

    def delete(self, reference: V1Service):
        return self.api.delete_namespaced_service(
            reference.metadata.name, self.namespace
        )

    def retrieve(self) -> V1Service:
        return self.api.read_namespaced_service(
            f"passbook-outpost-{self.outpost.name}", self.namespace
        )

    def update(self, current: V1Service, reference: V1Service):
        return self.api.patch_namespaced_service(
            current.metadata.name, self.namespace, reference
        )
