"""k8s utils"""
from pathlib import Path


def get_namespace() -> str:
    """Get the namespace if we're running in a pod, otherwise default to default"""
    path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
    if path.exists():
        with open(path, "r") as _namespace_file:
            return _namespace_file.read()
    return "default"
