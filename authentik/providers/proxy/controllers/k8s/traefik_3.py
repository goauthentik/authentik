"""Kubernetes Traefik Middleware Reconciler"""
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from dacite.core import from_dict
from kubernetes.client import ApiextensionsV1Api, CustomObjectsApi

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


@dataclass
class TraefikMiddlewareSpecForwardAuth:
    """traefik middleware forwardAuth spec"""

    address: str
    # pylint: disable=invalid-name
    authResponseHeadersRegex: str = field(default="")
    # pylint: disable=invalid-name
    authResponseHeaders: list[str] = field(default_factory=list)
    # pylint: disable=invalid-name
    trustForwardHeader: bool = field(default=True)


@dataclass
class TraefikMiddlewareSpec:
    """Traefik middleware spec"""

    # pylint: disable=invalid-name
    forwardAuth: TraefikMiddlewareSpecForwardAuth


@dataclass
class TraefikMiddlewareMetadata:
    """Traefik Middleware metadata"""

    name: str
    namespace: str
    labels: dict = field(default_factory=dict)


@dataclass
class TraefikMiddleware:
    """Traefik Middleware"""

    # pylint: disable=invalid-name
    apiVersion: str
    kind: str
    metadata: TraefikMiddlewareMetadata
    spec: TraefikMiddlewareSpec


class Traefik3MiddlewareReconciler(KubernetesObjectReconciler[TraefikMiddleware]):
    """Kubernetes Traefik Middleware Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        """Initialize the Traefik3MiddlewareReconciler.

        This method initializes the Traefik3MiddlewareReconciler class by setting the
        controller attribute and initializing some other attributes.

        Parameters:
            controller (KubernetesController): The Kubernetes controller object.

        Returns:
            None
        """
        super().__init__(controller)
        self.api_ex = ApiextensionsV1Api(controller.client)
        self.api = CustomObjectsApi(controller.client)
        self.crd_name = "middlewares.traefik.io"
        self.crd_group = "traefik.io"
        self.crd_version = "v1alpha1"
        self.crd_plural = "middlewares"

    @staticmethod
    def reconciler_name() -> str:
        """Return the name of the reconciler.

        This method returns the name of the reconciler as a string.

        Returns:
            str: The name of the reconciler.
        """
        return "traefik middleware"

    @property
    def noop(self) -> bool:
        """Check if the reconciler is a no-op.

        This method checks if the reconciler is a no-op by performing two checks:
        - Checking if there are any ProxyProvider objects with specific criteria.
        - Checking if the custom resource definition for the middleware exists.

        Returns:
            bool: True if the reconciler is a no-op, False otherwise.
        """
        if not ProxyProvider.objects.filter(
            outpost__in=[self.controller.outpost],
            mode__in=[ProxyMode.FORWARD_SINGLE, ProxyMode.FORWARD_DOMAIN],
        ).exists():
            self.logger.debug("No providers with forward auth enabled.")
            return True
        if not self.crd_exists():
            self.logger.debug("CRD doesn't exist")
            return True
        return False

    def crd_exists(self) -> bool:
        """Check if the traefik middleware exists.

        This method checks if the traefik middleware exists by querying the Kubernetes API
        using the CustomObjectsApi and ApiextensionsV1Api.

        Returns:
            bool: True if the middleware exists, False otherwise.
        """
        return bool(
            len(
                self.api_ex.list_custom_resource_definition(
                    field_selector=f"metadata.name={self.crd_name}"
                ).items
            )
        )

    def reconcile(self, current: TraefikMiddleware, reference: TraefikMiddleware):
        """
        Reconcile the 'current' and 'reference' TraefikMiddleware objects.

        This method checks if the 'current' and 'reference' objects are in sync by comparing
        various attributes. If any of the attributes differ, a 'NeedsUpdate' exception is raised.

        Parameters:
            current (TraefikMiddleware): The current TraefikMiddleware object.
            reference (TraefikMiddleware): The reference TraefikMiddleware object.

        Raises:
            NeedsUpdate: If any of the attributes of the 'current' and 'reference' objects differ.
        """
        super().reconcile(current, reference)
        if current.spec.forwardAuth.address != reference.spec.forwardAuth.address:
            raise NeedsUpdate()
        if (
            current.spec.forwardAuth.authResponseHeadersRegex
            != reference.spec.forwardAuth.authResponseHeadersRegex
        ):
            raise NeedsUpdate()
        # Ensure all of our headers are set, others can be added by the user.
        if not set(current.spec.forwardAuth.authResponseHeaders).issubset(
            reference.spec.forwardAuth.authResponseHeaders
        ):
            raise NeedsUpdate()

    def get_reference_object(self) -> TraefikMiddleware:
        """Get deployment object for outpost"""
        return TraefikMiddleware(
            apiVersion=f"{self.crd_group}/{self.crd_version}",
            kind="Middleware",
            metadata=TraefikMiddlewareMetadata(
                name=self.name,
                namespace=self.namespace,
                labels=self.get_object_meta().labels,
            ),
            spec=TraefikMiddlewareSpec(
                forwardAuth=TraefikMiddlewareSpecForwardAuth(
                    address=(
                        f"http://{self.name}.{self.namespace}:9000/"
                        "outpost.goauthentik.io/auth/traefik"
                    ),
                    authResponseHeaders=[
                        "X-authentik-username",
                        "X-authentik-groups",
                        "X-authentik-email",
                        "X-authentik-name",
                        "X-authentik-uid",
                        "X-authentik-jwt",
                        "X-authentik-meta-jwks",
                        "X-authentik-meta-outpost",
                        "X-authentik-meta-provider",
                        "X-authentik-meta-app",
                        "X-authentik-meta-version",
                    ],
                    authResponseHeadersRegex="",
                    trustForwardHeader=True,
                )
            ),
        )

    def create(self, reference: TraefikMiddleware):
        """
        Create a new custom object.

        This method creates a new custom object in the Kubernetes cluster using the Kubernetes Python client library. The custom object is created by making an API call to the cluster with the specified parameters.

        Parameters:
            reference (TraefikMiddleware): The reference object used to create the custom object.

        Returns:
            The response from the API call.
        """
        return self.api.create_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )

    def delete(self, reference: TraefikMiddleware):
        """
        Delete an existing custom object.

        This method deletes an existing custom object from the Kubernetes cluster using the Kubernetes Python client library. The custom object is deleted by making an API call to the cluster with the specified parameters.

        Parameters:
            reference (TraefikMiddleware): The reference object used to delete the custom object.

        Returns:
            The response from the API call.
        """
        return self.api.delete_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
        )

    def retrieve(self) -> TraefikMiddleware:
        """
        Retrieve an existing custom object.

        This method retrieves an existing custom object from the Kubernetes cluster using the Kubernetes Python client library. The custom object is retrieved by making an API call to the cluster with the specified parameters.

        Returns:
            The retrieved custom object.
        """
        return from_dict(
            TraefikMiddleware,
            self.api.get_namespaced_custom_object(
                group=self.crd_group,
                version=self.crd_version,
                plural=self.crd_plural,
                namespace=self.namespace,
                name=self.name,
            ),
        )

    def update(self, current: TraefikMiddleware, reference: TraefikMiddleware):
        """
        Update an existing custom object.

        This method updates an existing custom object in the Kubernetes cluster using the Kubernetes Python client library. The custom object is updated by making an API call to the cluster with the specified parameters.

        Parameters:
            current (TraefikMiddleware): The current object representing the existing custom object.
            reference (TraefikMiddleware): The reference object used to update the custom object.

        Returns:
            The response from the API call.
        """
        return self.api.patch_namespaced_custom_object(
            group=self.crd_group,
            version=self.crd_version,
            plural=self.crd_plural,
            namespace=self.namespace,
            name=self.name,
            body=asdict(reference),
            field_manager=FIELD_MANAGER,
        )
