"""Base Kubernetes Reconciler"""
from typing import TYPE_CHECKING, Generic, TypeVar

from kubernetes.client import V1ObjectMeta
from kubernetes.client.rest import ApiException
from structlog import get_logger

from authentik import __version__
from authentik.lib.sentry import SentryIgnoredException

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController

# pylint: disable=invalid-name
T = TypeVar("T")


class ReconcileTrigger(SentryIgnoredException):
    """Base trigger raised by child classes to notify us"""


class NeedsRecreate(ReconcileTrigger):
    """Exception to trigger a complete recreate of the Kubernetes Object"""


class NeedsUpdate(ReconcileTrigger):
    """Exception to trigger an update to the Kubernetes Object"""


class KubernetesObjectReconciler(Generic[T]):
    """Base Kubernetes Reconciler, handles the basic logic."""

    controller: "KubernetesController"

    def __init__(self, controller: "KubernetesController"):
        self.controller = controller
        self.namespace = controller.outpost.config.kubernetes_namespace
        self.logger = get_logger()

    @property
    def name(self) -> str:
        """Get the name of the object this reconciler manages"""
        raise NotImplementedError

    def up(self):
        """Create object if it doesn't exist, update if needed or recreate if needed."""
        current = None
        reference = self.get_reference_object()
        try:
            try:
                current = self.retrieve()
            except ApiException as exc:
                if exc.status == 404:
                    self.logger.debug("Failed to get current, triggering recreate")
                    raise NeedsRecreate from exc
                self.logger.debug("Other unhandled error", exc=exc)
                raise exc
            else:
                self.logger.debug("Got current, running reconcile")
                self.reconcile(current, reference)
        except NeedsRecreate:
            self.logger.debug("Recreate requested")
            if current:
                self.logger.debug("Deleted old")
                self.delete(current)
            else:
                self.logger.debug("No old found, creating")
            self.logger.debug("Created")
            self.create(reference)
        except NeedsUpdate:
            self.logger.debug("Updating")
            self.update(current, reference)
        else:
            self.logger.debug("Nothing to do...")

    def down(self):
        """Delete object if found"""
        try:
            current = self.retrieve()
            self.delete(current)
            self.logger.debug("Removing")
        except ApiException as exc:
            if exc.status == 404:
                self.logger.debug("Failed to get current, assuming non-existant")
                return
            self.logger.debug("Other unhandled error", exc=exc)
            raise exc

    def get_reference_object(self) -> T:
        """Return object as it should be"""
        raise NotImplementedError

    def reconcile(self, current: T, reference: T):
        """Check what operations should be done, should be raised as
        ReconcileTrigger"""
        if current.metadata.annotations != reference.metadata.annotations:
            raise NeedsUpdate()

    def create(self, reference: T):
        """API Wrapper to create object"""
        raise NotImplementedError

    def retrieve(self) -> T:
        """API Wrapper to retrive object"""
        raise NotImplementedError

    def delete(self, reference: T):
        """API Wrapper to delete object"""
        raise NotImplementedError

    def update(self, current: T, reference: T):
        """API Wrapper to update object"""
        raise NotImplementedError

    def get_object_meta(self, **kwargs) -> V1ObjectMeta:
        """Get common object metadata"""
        return V1ObjectMeta(
            namespace=self.namespace,
            labels={
                "app.kubernetes.io/name": f"authentik-{self.controller.outpost.type.lower()}",
                "app.kubernetes.io/instance": self.controller.outpost.name,
                "app.kubernetes.io/version": __version__,
                "app.kubernetes.io/managed-by": "goauthentik.io",
                "goauthentik.io/outpost-uuid": self.controller.outpost.uuid.hex,
            },
            **kwargs,
        )
