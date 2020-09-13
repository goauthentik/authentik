"""Kubernetes deployment controller"""
from base64 import b64encode
from io import StringIO

from kubernetes.client import (
    V1Container,
    V1ContainerPort,
    V1Deployment,
    V1DeploymentSpec,
    V1EnvVar,
    V1EnvVarSource,
    V1LabelSelector,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1Secret,
    V1SecretKeySelector,
    V1Service,
    V1ServicePort,
    V1ServiceSpec,
)
from yaml import dump_all

from passbook import __version__
from passbook.outposts.controllers.base import BaseController


def b64encode_str(input_string: str) -> str:
    """base64 encode string"""
    return b64encode(input_string.encode()).decode()


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    image_base = "beryju/passbook"

    def run(self):
        """Called by scheduled task to reconcile deployment/service/etc"""
        # TODO

    def get_static_deployment(self) -> str:
        with StringIO() as _str:
            dump_all(
                [
                    self.get_deployment_secret().to_dict(),
                    self.get_deployment().to_dict(),
                    self.get_service().to_dict(),
                ],
                stream=_str,
                default_flow_style=False,
            )
            return _str.getvalue()

    def get_object_meta(self, **kwargs) -> V1ObjectMeta:
        """Get common object metadata"""
        return V1ObjectMeta(
            namespace="self.instance.namespace",
            labels={
                "app.kubernetes.io/name": f"passbook-{self.outpost.type.lower()}",
                "app.kubernetes.io/instance": self.outpost.name,
                "app.kubernetes.io/version": __version__,
                "app.kubernetes.io/managed-by": "passbook.beryju.org",
                "passbook.beryju.org/outpost/uuid": self.outpost.uuid.hex,
            },
            **kwargs,
        )

    def get_deployment_secret(self) -> V1Secret:
        """Get secret with token and passbook host"""
        return V1Secret(
            api_version="v1",
            kind="secret",
            type="Opaque",
            metadata=self.get_object_meta(
                name=f"passbook-outpost-{self.outpost.name}-api"
            ),
            data={
                "passbook_host": b64encode_str(self.outpost.config.passbook_host),
                "passbook_host_insecure": b64encode_str(
                    str(self.outpost.config.passbook_host_insecure)
                ),
                "token": b64encode_str(self.outpost.token.token_uuid.hex),
            },
        )

    def get_service(self) -> V1Service:
        """Get service object for outpost based on ports defined"""
        meta = self.get_object_meta(name=f"passbook-outpost-{self.outpost.name}")
        ports = []
        for port_name, port in self.deployment_ports.items():
            ports.append(V1ServicePort(name=port_name, port=port))
        return V1Service(
            api_version="v1",
            kind="service",
            metadata=meta,
            spec=V1ServiceSpec(ports=ports, selector=meta.labels, type="ClusterIP"),
        )

    def get_deployment(self) -> V1Deployment:
        """Get deployment object for outpost"""
        # Generate V1ContainerPort objects
        container_ports = []
        for port_name, port in self.deployment_ports.items():
            container_ports.append(V1ContainerPort(container_port=port, name=port_name))
        meta = self.get_object_meta(name=f"passbook-outpost-{self.outpost.name}")
        return V1Deployment(
            api_version="apps/v1",
            kind="deployment",
            metadata=meta,
            spec=V1DeploymentSpec(
                replicas=1,
                selector=V1LabelSelector(match_labels=meta.labels),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(labels=meta.labels),
                    spec=V1PodSpec(
                        containers=[
                            V1Container(
                                name=self.outpost.type,
                                image=f"{self.image_base}-{self.outpost.type}:{__version__}",
                                ports=container_ports,
                                env=[
                                    V1EnvVar(
                                        name="PASSBOOK_HOST",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=f"passbook-outpost-{self.outpost.name}-api",
                                                key="passbook_host",
                                            )
                                        ),
                                    ),
                                    V1EnvVar(
                                        name="PASSBOOK_TOKEN",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=f"passbook-outpost-{self.outpost.name}-api",
                                                key="token",
                                            )
                                        ),
                                    ),
                                    V1EnvVar(
                                        name="PASSBOOK_INSECURE",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=f"passbook-outpost-{self.outpost.name}-api",
                                                key="passbook_host_insecure",
                                            )
                                        ),
                                    ),
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )
