"""Kubernetes Secret Reconciler"""
from base64 import b64encode
from typing import TYPE_CHECKING

from kubernetes.client import CoreV1Api, V1Secret

from passbook.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsUpdate,
)

if TYPE_CHECKING:
    from passbook.outposts.controllers.kubernetes import KubernetesController


def b64string(source: str) -> str:
    """Base64 Encode string"""
    return b64encode(source.encode()).decode("utf-8")


class SecretReconciler(KubernetesObjectReconciler[V1Secret]):
    """Kubernetes Secret Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api = CoreV1Api()

    @property
    def name(self) -> str:
        return f"passbook-outpost-{self.controller.outpost.uuid.hex}-api"

    def reconcile(self, current: V1Secret, reference: V1Secret):
        for key in reference.data.keys():
            if current.data[key] != reference.data[key]:
                raise NeedsUpdate()

    def get_reference_object(self) -> V1Secret:
        """Get deployment object for outpost"""
        meta = self.get_object_meta(name=self.name)
        return V1Secret(
            metadata=meta,
            data={
                "passbook_host": b64string(
                    self.controller.outpost.config.passbook_host
                ),
                "passbook_host_insecure": b64string(
                    str(self.controller.outpost.config.passbook_host_insecure)
                ),
                "token": b64string(self.controller.outpost.token.token_uuid.hex),
            },
        )

    def create(self, reference: V1Secret):
        return self.api.create_namespaced_secret(self.namespace, reference)

    def delete(self, reference: V1Secret):
        return self.api.delete_namespaced_secret(
            reference.metadata.name, self.namespace
        )

    def retrieve(self) -> V1Secret:
        return self.api.read_namespaced_secret(self.name, self.namespace)

    def update(self, current: V1Secret, reference: V1Secret):
        return self.api.patch_namespaced_secret(
            current.metadata.name, self.namespace, reference
        )
