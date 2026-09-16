"""k8s utils"""

from pathlib import Path
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from kubernetes.client.configuration import Configuration
from kubernetes.client.models.v1_container_port import V1ContainerPort
from kubernetes.client.models.v1_service_port import V1ServicePort
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME
from kubernetes.config.kube_config import load_kube_config_from_dict

from authentik.outposts.controllers.k8s.triggers import NeedsRecreate

if TYPE_CHECKING:
    from authentik.crypto.secrets.models import Secret


def validate_kubeconfig(secret: Secret) -> None:
    """Validate the credential using the same loader as the Kubernetes client."""
    try:
        load_kube_config_from_dict(secret.get_json(), client_configuration=Configuration())
    except ConfigException, ValueError, AttributeError, TypeError:
        raise ValidationError(_("Invalid kubeconfig")) from None


def get_namespace() -> str:
    """Get the namespace if we're running in a pod, otherwise default to default"""
    path = Path(SERVICE_TOKEN_FILENAME.replace("token", "namespace"))
    if path.exists():
        with open(path, encoding="utf8") as _namespace_file:
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
