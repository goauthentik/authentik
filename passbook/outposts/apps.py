"""passbook outposts app config"""
from importlib import import_module
from os import R_OK, access
from os.path import expanduser
from pathlib import Path
from socket import gethostname
from urllib.parse import urlparse

from django.apps import AppConfig
from django.db import ProgrammingError
from docker.constants import DEFAULT_UNIX_SOCKET
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION
from structlog import get_logger

LOGGER = get_logger()


class PassbookOutpostConfig(AppConfig):
    """passbook outposts app config"""

    name = "passbook.outposts"
    label = "passbook_outposts"
    mountpoint = "outposts/"
    verbose_name = "passbook Outpost"

    def ready(self):
        import_module("passbook.outposts.signals")
        try:
            self.init_local_connection()
        except (ProgrammingError):
            pass

    def init_local_connection(self):
        # Check if local kubernetes or docker connections should be created
        from passbook.outposts.models import (
            KubernetesServiceConnection,
            DockerServiceConnection,
        )

        if Path(SERVICE_TOKEN_FILENAME).exists():
            LOGGER.debug("Detected in-cluster Kubernetes Config")
            if not KubernetesServiceConnection.objects.filter(local=True).exists():
                LOGGER.debug("Created Service Connection for in-cluster")
                KubernetesServiceConnection.objects.create(
                    name="Local Kubernetes Cluster", local=True, config={}
                )
        # For development, check for the existence of a kubeconfig file
        kubeconfig_path = expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
        if Path(kubeconfig_path).exists():
            LOGGER.debug("Detected kubeconfig")
            if not KubernetesServiceConnection.objects.filter(
                name=gethostname()
            ).exists():
                LOGGER.debug("Creating kubeconfig Service Connection")
                with open(kubeconfig_path, "r") as _kubeconfig:
                    KubernetesServiceConnection.objects.create(
                        name=gethostname(), config=_kubeconfig.read()
                    )
        unix_socket_path = urlparse(DEFAULT_UNIX_SOCKET).path
        socket = Path(unix_socket_path)
        if socket.exists() and access(socket, R_OK):
            LOGGER.debug("Detected local docker socket")
            if not DockerServiceConnection.objects.filter(local=True).exists():
                LOGGER.debug("Created Service Connection for docker")
                DockerServiceConnection.objects.create(
                    name="Local Docker connection",
                    local=True,
                    url=unix_socket_path,
                    tls=True,
                )
