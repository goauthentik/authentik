"""k8s utils"""
from pathlib import Path

from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME


def get_namespace() -> str:
    """Get the namespace if we're running in a pod, otherwise default to default"""
    path = Path(SERVICE_TOKEN_FILENAME.replace("token", "namespace"))
    if path.exists():
        with open(path, "r", encoding="utf8") as _namespace_file:
            return _namespace_file.read()
    return "default"
