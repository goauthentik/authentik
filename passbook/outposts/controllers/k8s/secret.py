"""Kubernetes Secret Reconciler"""
from base64 import b64encode

from kubernetes.client import CoreV1Api, V1Secret

from passbook.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsUpdate,
)
from passbook.outposts.models import Outpost


def b64string(source: str) -> str:
    """Base64 Encode string"""
    return b64encode(source.encode()).decode("utf-8")


class SecretReconciler(KubernetesObjectReconciler[V1Secret]):
    """Kubernetes Secret Reconciler"""

    def __init__(self, outpost: Outpost) -> None:
        super().__init__(outpost)
        self.api = CoreV1Api()

    def reconcile(self, current: V1Secret, reference: V1Secret):
        for key in reference.data.keys():
            if current.data[key] != reference.data[key]:
                raise NeedsUpdate()

    def get_reference_object(self) -> V1Secret:
        """Get deployment object for outpost"""
        meta = self.get_object_meta(name=f"passbook-outpost-{self.outpost.name}-api")
        return V1Secret(
            metadata=meta,
            data={
                "passbook_host": b64string(self.outpost.config.passbook_host),
                "passbook_host_insecure": b64string(
                    str(self.outpost.config.passbook_host_insecure)
                ),
                "token": b64string(self.outpost.token.token_uuid.hex),
            },
        )

    def create(self, reference: V1Secret):
        return self.api.create_namespaced_secret(self.namespace, reference)

    def delete(self, reference: V1Secret):
        return self.api.delete_namespaced_secret(
            reference.metadata.name, self.namespace
        )

    def retrieve(self) -> V1Secret:
        return self.api.read_namespaced_secret(
            f"passbook-outpost-{self.outpost.name}-api", self.namespace
        )

    def update(self, current: V1Secret, reference: V1Secret):
        return self.api.patch_namespaced_secret(
            current.metadata.name, self.namespace, reference
        )
