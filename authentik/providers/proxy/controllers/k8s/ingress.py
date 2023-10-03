"""Kubernetes Ingress Reconciler"""
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from kubernetes.client import (
    NetworkingV1Api,
    V1HTTPIngressPath,
    V1HTTPIngressRuleValue,
    V1Ingress,
    V1IngressSpec,
    V1IngressTLS,
    V1ServiceBackendPort,
)
from kubernetes.client.models.v1_ingress_backend import V1IngressBackend
from kubernetes.client.models.v1_ingress_rule import V1IngressRule
from kubernetes.client.models.v1_ingress_service_backend import V1IngressServiceBackend

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsRecreate, NeedsUpdate
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class IngressReconciler(KubernetesObjectReconciler[V1Ingress]):
    """Kubernetes Ingress Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        """Initialize the IngressReconciler.

        Args:
            controller (KubernetesController): The Kubernetes controller.
        """
        super().__init__(controller)
        self.api = NetworkingV1Api(controller.client)

    @staticmethod
    def reconciler_name() -> str:
        """Return the reconciler name.

        Returns:
            str: The reconciler name.
        """
        return "ingress"

    def _check_annotations(self, reference: V1Ingress):
        """Check that all annotations *we* set are correct.

        Args:
            reference (V1Ingress): The reference ingress object.

        Raises:
            NeedsUpdate: If annotations are incorrect.
        """
        for key, value in self.get_ingress_annotations().items():
            if key not in reference.metadata.annotations:
                raise NeedsUpdate()
            if reference.metadata.annotations[key] != value:
                raise NeedsUpdate()

    def reconcile(self, current: V1Ingress, reference: V1Ingress):
        """
        Reconcile the current and reference V1Ingress objects.

        This method compares the current and reference V1Ingress objects and raises NeedsUpdate
        or NeedsRecreate exceptions if certain conditions are met.

        Parameters:
            current (V1Ingress): The current V1Ingress object.
            reference (V1Ingress): The reference V1Ingress object.
        """
        super().reconcile(current, reference)
        self._check_annotations(reference)
        # Create a list of all expected host and tls hosts
        expected_hosts = []
        expected_hosts_tls = []
        for proxy_provider in ProxyProvider.objects.filter(
            outpost__in=[self.controller.outpost],
        ):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            expected_hosts.append(external_host_name.hostname)
            if external_host_name.scheme == "https":
                expected_hosts_tls.append(external_host_name.hostname)
        expected_hosts.sort()
        expected_hosts_tls.sort()

        have_hosts = [rule.host for rule in current.spec.rules]
        have_hosts.sort()

        have_hosts_tls = []
        if current.spec.tls:
            for tls_config in current.spec.tls:
                if not tls_config:
                    continue
                if tls_config.hosts:
                    have_hosts_tls += tls_config.hosts
                if (
                    tls_config.secret_name
                    != self.controller.outpost.config.kubernetes_ingress_secret_name
                ):
                    raise NeedsUpdate()
        have_hosts_tls.sort()

        if have_hosts != expected_hosts:
            raise NeedsUpdate()
        if have_hosts_tls != expected_hosts_tls:
            raise NeedsUpdate()
        # If we have a current ingress, which wouldn't have any hosts, raise
        # NeedsRecreate() so that its deleted, and check hosts on create
        if len(have_hosts) < 1:
            raise NeedsRecreate()

    def get_ingress_annotations(self) -> dict[str, str]:
        """Get ingress annotations"""
        annotations = {
            # Ensure that with multiple proxy replicas deployed, the same CSRF request
            # goes to the same pod
            "nginx.ingress.kubernetes.io/affinity": "cookie",
            "traefik.ingress.kubernetes.io/affinity": "true",
            # Buffer sizes for large headers with JWTs
            "nginx.ingress.kubernetes.io/proxy-buffers-number": "4",
            "nginx.ingress.kubernetes.io/proxy-buffer-size": "16k",
            # Enable TLS in traefik
            "traefik.ingress.kubernetes.io/router.tls": "true",
        }
        annotations.update(self.controller.outpost.config.kubernetes_ingress_annotations)
        return annotations

    def get_reference_object(self) -> V1Ingress:
        """Get deployment object for outpost"""
        meta = self.get_object_meta(
            name=self.name,
            annotations=self.get_ingress_annotations(),
        )
        rules = []
        tls_hosts = []
        for proxy_provider in ProxyProvider.objects.filter(
            outpost__in=[self.controller.outpost],
        ):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            if external_host_name.scheme == "https":
                tls_hosts.append(external_host_name.hostname)
            if proxy_provider.mode in [
                ProxyMode.FORWARD_SINGLE,
                ProxyMode.FORWARD_DOMAIN,
            ]:
                rule = V1IngressRule(
                    host=external_host_name.hostname,
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name=self.name,
                                        port=V1ServiceBackendPort(name="http"),
                                    ),
                                ),
                                path="/outpost.goauthentik.io",
                                path_type="Prefix",
                            )
                        ]
                    ),
                )
            else:
                rule = V1IngressRule(
                    host=external_host_name.hostname,
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name=self.name,
                                        port=V1ServiceBackendPort(name="http"),
                                    ),
                                ),
                                path="/",
                                path_type="Prefix",
                            )
                        ]
                    ),
                )
            rules.append(rule)
        tls_config = None
        if tls_hosts:
            tls_config = V1IngressTLS(
                hosts=tls_hosts,
                secret_name=self.controller.outpost.config.kubernetes_ingress_secret_name,
            )
        spec = V1IngressSpec(
            rules=rules,
            tls=[tls_config],
        )
        if self.controller.outpost.config.kubernetes_ingress_class_name:
            spec.ingress_class_name = self.controller.outpost.config.kubernetes_ingress_class_name
        return V1Ingress(
            metadata=meta,
            spec=spec,
        )

    def create(self, reference: V1Ingress):
        """
        Create a new ingress resource based on the provided reference object.

        This method interacts with the Kubernetes API to create a new ingress resource
        using the provided reference object. If no hosts are defined in the reference,
        the method logs a debug message and returns None.

        Parameters:
            reference (V1Ingress): The reference object for creating the ingress resource.

        Returns:
            None: If no hosts are defined in the reference.
            V1Ingress: The created ingress resource.
        """
        if len(reference.spec.rules) < 1:
            self.logger.debug("No hosts defined, not creating ingress.")
            return None
        return self.api.create_namespaced_ingress(
            self.namespace, reference, field_manager=FIELD_MANAGER
        )

    def delete(self, reference: V1Ingress):
        """
        Delete an existing ingress resource.

        This method interacts with the Kubernetes API to delete an existing ingress resource
        based on the provided reference object.

        Parameters:
            reference (V1Ingress): The reference object for deleting the ingress resource.

        Returns:
            None
        """
        return self.api.delete_namespaced_ingress(reference.metadata.name, self.namespace)

    def retrieve(self) -> V1Ingress:
        """
        Retrieve an existing ingress resource based on its name.

        This method interacts with the Kubernetes API to retrieve an existing ingress resource
        based on its name.

        Returns:
            V1Ingress: The retrieved ingress resource.
        """
        return self.api.read_namespaced_ingress(self.name, self.namespace)

    def update(self, current: V1Ingress, reference: V1Ingress):
        """
        Update an existing ingress resource with the provided reference object.

        This method interacts with the Kubernetes API to update an existing ingress resource
        with the provided reference object.

        Parameters:
            current (V1Ingress): The current ingress resource to be updated.
            reference (V1Ingress): The reference object for updating the ingress resource.

        Returns:
            None
        """
        return self.api.patch_namespaced_ingress(
            current.metadata.name,
            self.namespace,
            reference,
            field_manager=FIELD_MANAGER,
        )
