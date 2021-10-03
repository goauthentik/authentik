"""k8s utils"""
from pathlib import Path

from kubernetes.client.models.v1_container_port import V1ContainerPort
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME

from authentik.outposts.controllers.k8s.triggers import NeedsRecreate


def get_namespace() -> str:
    """Get the namespace if we're running in a pod, otherwise default to default"""
    path = Path(SERVICE_TOKEN_FILENAME.replace("token", "namespace"))
    if path.exists():
        with open(path, "r", encoding="utf8") as _namespace_file:
            return _namespace_file.read()
    return "default"


def compare_ports(current: list[V1ContainerPort], reference: list[V1ContainerPort]):
    """Compare ports of a list"""
    if len(current) != len(reference):
        raise NeedsRecreate()
    for port in reference:
        if port not in current:
            raise NeedsRecreate()
