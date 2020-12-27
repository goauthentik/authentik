"""Kubernetes Ingress Reconciler"""
from typing import TYPE_CHECKING, Dict
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
from kubernetes.client.models.networking_v1beta1_ingress_rule import (
    NetworkingV1beta1IngressRule,
)

from authentik.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsUpdate,
)
from authentik.providers.proxy.models import ProxyProvider

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class IngressReconciler(KubernetesObjectReconciler[NetworkingV1beta1Ingress]):
    """Kubernetes Ingress Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api = NetworkingV1beta1Api(controller.client)

    @property
    def name(self) -> str:
        return f"authentik-outpost-{self.controller.outpost.uuid.hex}"

    def reconcile(
        self, current: NetworkingV1beta1Ingress, reference: NetworkingV1beta1Ingress
    ):
        # Create a list of all expected host and tls hosts
        expected_hosts = []
        expected_hosts_tls = []
        for proxy_provider in ProxyProvider.objects.filter(
            outpost__in=[self.controller.outpost]
        ):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            expected_hosts.append(external_host_name.hostname)
            if external_host_name.scheme == "https":
                expected_hosts_tls.append(external_host_name.hostname)
        expected_hosts.sort()
        expected_hosts_tls.sort()

        have_hosts = [rule.host for rule in reference.spec.rules]
        have_hosts.sort()

        have_hosts_tls = []
        for tls_config in reference.spec.tls:
            if tls_config:
                have_hosts_tls += tls_config.hosts
        have_hosts_tls.sort()

        if have_hosts != expected_hosts:
            raise NeedsUpdate()
        if have_hosts_tls != expected_hosts_tls:
            raise NeedsUpdate()

    def get_ingress_annotations(self) -> Dict[str, str]:
        """Get ingress annotations"""
        annotations = {
            # Ensure that with multiple proxy replicas deployed, the same CSRF request
            # goes to the same pod
            "nginx.ingress.kubernetes.io/affinity": "cookie",
            "traefik.ingress.kubernetes.io/affinity": "true",
            "nginx.ingress.kubernetes.io/proxy-buffers-number": "4",
            "nginx.ingress.kubernetes.io/proxy-buffer-size": "16k",
        }
        annotations.update(
            self.controller.outpost.config.kubernetes_ingress_annotations
        )
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
            outpost__in=[self.controller.outpost]
        ):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            if external_host_name.scheme == "https":
                tls_hosts.append(external_host_name.hostname)
            rule = NetworkingV1beta1IngressRule(
                host=external_host_name.hostname,
                http=NetworkingV1beta1HTTPIngressRuleValue(
                    paths=[
                        NetworkingV1beta1HTTPIngressPath(
                            backend=NetworkingV1beta1IngressBackend(
                                service_name=self.name,
                                service_port=self.controller.deployment_ports["http"],
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
        return self.api.create_namespaced_ingress(self.namespace, reference)

    def delete(self, reference: NetworkingV1beta1Ingress):
        return self.api.delete_namespaced_ingress(
            reference.metadata.name, self.namespace
        )

    def retrieve(self) -> NetworkingV1beta1Ingress:
        return self.api.read_namespaced_ingress(self.name, self.namespace)

    def update(
        self, current: NetworkingV1beta1Ingress, reference: NetworkingV1beta1Ingress
    ):
        return self.api.patch_namespaced_ingress(
            current.metadata.name, self.namespace, reference
        )
