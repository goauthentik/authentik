"""k8s utils"""
from pathlib import Path
from typing import Optional

from kubernetes.client.models.v1_container_port import V1ContainerPort
from kubernetes.client.models.v1_service_port import V1ServicePort
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME

from authentik.outposts.controllers.k8s.triggers import NeedsRecreate


def get_namespace() -> str:
    """Get the namespace if we're running in a pod, otherwise default to default"""
    path = Path(SERVICE_TOKEN_FILENAME.replace("token", "namespace"))
    if path.exists():
        with open(path, "r", encoding="utf8") as _namespace_file:
            return _namespace_file.read()
    return "default"


def compare_port(
    current: V1ServicePort | V1ContainerPort, reference: V1ServicePort | V1ContainerPort
) -> bool:
    """Compare a single port"""
    if current.name != reference.name:
        return False
    if current.protocol != reference.protocol:
        return False
    if isinstance(current, V1ServicePort) and isinstance(reference, V1ServicePort):
        # We only care about the target port
        if current.target_port != reference.target_port:
            return False
    if isinstance(current, V1ContainerPort) and isinstance(reference, V1ContainerPort):
        # We only care about the target port
        if current.container_port != reference.container_port:
            return False
    return True


def compare_ports(
    current: Optional[list[V1ServicePort | V1ContainerPort]],
    reference: Optional[list[V1ServicePort | V1ContainerPort]],
):
    """Compare ports of a list"""
    if not current or not reference:
        raise NeedsRecreate()
    if len(current) != len(reference):
        raise NeedsRecreate()
    for port in reference:
        if not any(compare_port(port, current_port) for current_port in current):
            raise NeedsRecreate()
