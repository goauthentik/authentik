"""Base Kubernetes Reconciler"""
from dataclasses import asdict
from json import dumps
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from dacite.core import from_dict
from django.utils.text import slugify
from jsonpatch import JsonPatchConflict, JsonPatchException, JsonPatchTestFailed, apply_patch
from kubernetes.client import ApiClient, V1ObjectMeta
from kubernetes.client.exceptions import ApiException, OpenApiException
from kubernetes.client.models.v1_deployment import V1Deployment
from kubernetes.client.models.v1_pod import V1Pod
from requests import Response
from structlog.stdlib import get_logger
from urllib3.exceptions import HTTPError

from authentik import __version__
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.controllers.base import ControllerException
from authentik.outposts.controllers.k8s.triggers import NeedsRecreate, NeedsUpdate

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController

T = TypeVar("T", V1Pod, V1Deployment)


def get_version() -> str:
    """Wrapper for __version__ to make testing easier"""
    return __version__


class KubernetesObjectReconciler(Generic[T]):
    """Base Kubernetes Reconciler, handles the basic logic."""

    controller: "KubernetesController"

    def __init__(self, controller: "KubernetesController"):
        self.controller = controller
        self.namespace = controller.outpost.config.kubernetes_namespace
        self.logger = get_logger().bind(type=self.__class__.__name__)

    def get_patch(self):
        """Get any patches that apply to this CRD"""
        patches = self.controller.outpost.config.kubernetes_json_patches
        if not patches:
            return None
        return patches.get(self.reconciler_name(), None)

    @property
    def is_embedded(self) -> bool:
        """Return true if the current outpost is embedded"""
        return self.controller.outpost.managed == MANAGED_OUTPOST

    @staticmethod
    def reconciler_name() -> str:
        """A name this reconciler is identified by in the configuration"""
        raise NotImplementedError

    @property
    def noop(self) -> bool:
        """Return true if this object should not be created/updated/deleted in this cluster"""
        return False

    @property
    def name(self) -> str:
        """Get the name of the object this reconciler manages"""
        return (
            self.controller.outpost.config.object_naming_template
            % {
                "name": slugify(self.controller.outpost.name),
                "uuid": self.controller.outpost.uuid.hex,
            }
        ).lower()

    def get_patched_reference_object(self) -> T:
        """Get patched reference object"""
        reference = self.get_reference_object()
        patch = self.get_patch()
        try:
            json = ApiClient().sanitize_for_serialization(reference)
        # Custom objects will not be known to the clients openapi types
        except AttributeError:
            json = asdict(reference)
        try:
            ref = json
            if patch is not None:
                ref = apply_patch(json, patch)
        except (JsonPatchException, JsonPatchConflict, JsonPatchTestFailed) as exc:
            raise ControllerException(f"JSON Patch failed: {exc}") from exc
        mock_response = Response()
        mock_response.data = dumps(ref)

        try:
            result = ApiClient().deserialize(mock_response, reference.__class__.__name__)
        # Custom objects will not be known to the clients openapi types
        except AttributeError:
            result = from_dict(reference.__class__, data=ref)

        return result

    # pylint: disable=invalid-name
    def up(self):
        """Create object if it doesn't exist, update if needed or recreate if needed."""
        current = None
        if self.noop:
            self.logger.debug("Object is noop")
            return
        reference = self.get_patched_reference_object()
        try:
            try:
                current = self.retrieve()
            except (OpenApiException, HTTPError) as exc:
                # pylint: disable=no-member
                if isinstance(exc, ApiException) and exc.status == 404:
                    self.logger.debug("Failed to get current, triggering recreate")
                    raise NeedsRecreate from exc
                self.logger.debug("Other unhandled error", exc=exc)
                raise exc
            self.reconcile(current, reference)
        except NeedsUpdate:
            try:
                self.update(current, reference)
                self.logger.debug("Updating")
            except (OpenApiException, HTTPError) as exc:
                # pylint: disable=no-member
                if isinstance(exc, ApiException) and exc.status == 422:
                    self.logger.debug("Failed to update current, triggering re-create")
                    self._recreate(current=current, reference=reference)
                    return
                self.logger.debug("Other unhandled error", exc=exc)
                raise exc
        except NeedsRecreate:
            self._recreate(current=current, reference=reference)
        else:
            self.logger.debug("Object is up-to-date.")

    def _recreate(self, reference: T, current: Optional[T] = None):
        """Recreate object"""
        self.logger.debug("Recreate requested")
        if current:
            self.logger.debug("Deleted old")
            self.delete(current)
        else:
            self.logger.debug("No old found, creating")
        self.logger.debug("Creating")
        self.create(reference)

    def down(self):
        """Delete object if found"""
        if self.noop:
            self.logger.debug("Object is noop")
            return
        try:
            current = self.retrieve()
            self.delete(current)
            self.logger.debug("Removing")
        except (OpenApiException, HTTPError) as exc:
            # pylint: disable=no-member
            if isinstance(exc, ApiException) and exc.status == 404:
                self.logger.debug("Failed to get current, assuming non-existent")
                return
            self.logger.debug("Other unhandled error", exc=exc)
            raise exc

    def get_reference_object(self) -> T:
        """Return object as it should be"""
        raise NotImplementedError

    def reconcile(self, current: T, reference: T):
        """Check what operations should be done, should be raised as
        ReconcileTrigger"""
        if current.metadata.labels != reference.metadata.labels:
            raise NeedsUpdate()

        patch = self.get_patch()
        if patch is not None:
            current_json = ApiClient().sanitize_for_serialization(current)

            try:
                if apply_patch(current_json, patch) != current_json:
                    raise NeedsUpdate()
            except (JsonPatchException, JsonPatchConflict, JsonPatchTestFailed) as exc:
                raise ControllerException(f"JSON Patch failed: {exc}") from exc

    def create(self, reference: T):
        """API Wrapper to create object"""
        raise NotImplementedError

    def retrieve(self) -> T:
        """API Wrapper to retrieve object"""
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
                "app.kubernetes.io/instance": slugify(self.controller.outpost.name),
                "app.kubernetes.io/managed-by": "goauthentik.io",
                "app.kubernetes.io/name": f"authentik-{self.controller.outpost.type.lower()}",
                "app.kubernetes.io/version": get_version(),
                "goauthentik.io/outpost-name": slugify(self.controller.outpost.name),
                "goauthentik.io/outpost-type": str(self.controller.outpost.type),
                "goauthentik.io/outpost-uuid": self.controller.outpost.uuid.hex,
            },
            **kwargs,
        )
