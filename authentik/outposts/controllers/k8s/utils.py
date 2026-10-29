"""k8s utils"""

from kubernetes.client.models.v1_container_port import V1ContainerPort
from kubernetes.client.models.v1_service_port import V1ServicePort

from authentik.outposts.controllers.k8s.triggers import NeedsRecreate


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
    current: list[V1ServicePort | V1ContainerPort] | None,
    reference: list[V1ServicePort | V1ContainerPort] | None,
):
    """Compare ports of a list"""
    if not current or not reference:
        raise NeedsRecreate()
    if len(current) != len(reference):
        raise NeedsRecreate()
    for port in reference:
        if not any(compare_port(port, current_port) for current_port in current):
            raise NeedsRecreate()
