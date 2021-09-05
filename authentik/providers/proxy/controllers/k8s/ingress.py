"""Kubernetes Ingress Reconciler"""
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from kubernetes.client import (
    NetworkingV1beta1Api,
    NetworkingV1beta1HTTPIngressPath,
    NetworkingV1beta1HTTPIngressRuleValue,
    NetworkingV1beta1Ingress,
    NetworkingV1beta1IngressBackend,
    NetworkingV1beta1IngressSpec,
    NetworkingV1beta1IngressTLS,
)
from kubernetes.client.models.networking_v1beta1_ingress_rule import NetworkingV1beta1IngressRule

from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsRecreate,
    NeedsUpdate,
)
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class IngressReconciler(KubernetesObjectReconciler[NetworkingV1beta1Ingress]):
    """Kubernetes Ingress Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api = NetworkingV1beta1Api(controller.client)

    def _check_annotations(self, reference: NetworkingV1beta1Ingress):
        """Check that all annotations *we* set are correct"""
        for key, value in self.get_ingress_annotations().items():
            if key not in reference.metadata.annotations:
                raise NeedsUpdate()
            if reference.metadata.annotations[key] != value:
                raise NeedsUpdate()

    def reconcile(self, current: NetworkingV1beta1Ingress, reference: NetworkingV1beta1Ingress):
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
                if tls_config and tls_config.hosts:
                    have_hosts_tls += tls_config.hosts
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
            "nginx.ingress.kubernetes.io/proxy-buffers-number": "4",
            "nginx.ingress.kubernetes.io/proxy-buffer-size": "16k",
        }
        annotations.update(self.controller.outpost.config.kubernetes_ingress_annotations)
        return annotations

    def get_reference_object(self) -> NetworkingV1beta1Ingress:
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
                rule = NetworkingV1beta1IngressRule(
                    host=external_host_name.hostname,
                    http=NetworkingV1beta1HTTPIngressRuleValue(
                        paths=[
                            NetworkingV1beta1HTTPIngressPath(
                                backend=NetworkingV1beta1IngressBackend(
                                    service_name=self.name,
                                    service_port="http",
                                ),
                                path="/akprox",
                            )
                        ]
                    ),
                )
            else:
                rule = NetworkingV1beta1IngressRule(
                    host=external_host_name.hostname,
                    http=NetworkingV1beta1HTTPIngressRuleValue(
                        paths=[
                            NetworkingV1beta1HTTPIngressPath(
                                backend=NetworkingV1beta1IngressBackend(
                                    service_name=self.name,
                                    service_port="http",
                                ),
                                path="/",
                            )
                        ]
                    ),
                )
            rules.append(rule)
        tls_config = None
        if tls_hosts:
            tls_config = NetworkingV1beta1IngressTLS(
                hosts=tls_hosts,
                secret_name=self.controller.outpost.config.kubernetes_ingress_secret_name,
            )
        return NetworkingV1beta1Ingress(
            metadata=meta,
            spec=NetworkingV1beta1IngressSpec(rules=rules, tls=[tls_config]),
        )

    def create(self, reference: NetworkingV1beta1Ingress):
        if len(reference.spec.rules) < 1:
            self.logger.debug("No hosts defined, not creating ingress.")
            return None
        return self.api.create_namespaced_ingress(
            self.namespace, reference, field_manager=FIELD_MANAGER
        )

    def delete(self, reference: NetworkingV1beta1Ingress):
        return self.api.delete_namespaced_ingress(reference.metadata.name, self.namespace)

    def retrieve(self) -> NetworkingV1beta1Ingress:
        return self.api.read_namespaced_ingress(self.name, self.namespace)

    def update(self, current: NetworkingV1beta1Ingress, reference: NetworkingV1beta1Ingress):
        return self.api.patch_namespaced_ingress(
            current.metadata.name,
            self.namespace,
            reference,
            field_manager=FIELD_MANAGER,
        )
