"""outpost tasks"""

from hashlib import sha256
from os import R_OK, access
from pathlib import Path
from socket import gethostname
from typing import Any
from urllib.parse import urlparse

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from docker.constants import DEFAULT_UNIX_SOCKET
from dramatiq.actor import actor
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION
from structlog.stdlib import get_logger
from yaml import safe_load

from authentik.lib.config import CONFIG
from authentik.outposts.consumer import OUTPOST_GROUP
from authentik.outposts.controllers.base import BaseController, ControllerException
from authentik.outposts.controllers.docker import DockerClient
from authentik.outposts.controllers.kubernetes import KubernetesClient
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
    OutpostServiceConnection,
    OutpostType,
    ServiceConnectionInvalid,
)
from authentik.providers.ldap.controllers.docker import LDAPDockerController
from authentik.providers.ldap.controllers.kubernetes import LDAPKubernetesController
from authentik.providers.proxy.controllers.docker import ProxyDockerController
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.rac.controllers.docker import RACDockerController
from authentik.providers.rac.controllers.kubernetes import RACKubernetesController
from authentik.providers.radius.controllers.docker import RadiusDockerController
from authentik.providers.radius.controllers.kubernetes import RadiusKubernetesController
from authentik.tasks.models import Task

LOGGER = get_logger()
CACHE_KEY_OUTPOST_DOWN = "goauthentik.io/outposts/teardown/%s"


def hash_session_key(session_key: str) -> str:
    """Hash the session key for sending session end signals"""
    return sha256(session_key.encode("ascii")).hexdigest()


def controller_for_outpost(outpost: Outpost) -> type[BaseController] | None:
    """Get a controller for the outpost, when a service connection is defined"""
    if not outpost.service_connection:
        return None
    service_connection = outpost.service_connection
    if outpost.type == OutpostType.PROXY:
        if isinstance(service_connection, DockerServiceConnection):
            return ProxyDockerController
        if isinstance(service_connection, KubernetesServiceConnection):
            return ProxyKubernetesController
    if outpost.type == OutpostType.LDAP:
        if isinstance(service_connection, DockerServiceConnection):
            return LDAPDockerController
        if isinstance(service_connection, KubernetesServiceConnection):
            return LDAPKubernetesController
    if outpost.type == OutpostType.RADIUS:
        if isinstance(service_connection, DockerServiceConnection):
            return RadiusDockerController
        if isinstance(service_connection, KubernetesServiceConnection):
            return RadiusKubernetesController
    if outpost.type == OutpostType.RAC:
        if isinstance(service_connection, DockerServiceConnection):
            return RACDockerController
        if isinstance(service_connection, KubernetesServiceConnection):
            return RACKubernetesController
    return None


@actor(description=_("Update cached state of service connection."))
def outpost_service_connection_monitor(connection_pk: Any):
    """Update cached state of a service connection"""
    connection: OutpostServiceConnection = (
        OutpostServiceConnection.objects.filter(pk=connection_pk).select_subclasses().first()
    )
    if not connection:
        return
    cls = None
    if isinstance(connection, DockerServiceConnection):
        cls = DockerClient
    if isinstance(connection, KubernetesServiceConnection):
        cls = KubernetesClient
    if not cls:
        LOGGER.warning("No class found for service connection", connection=connection)
        return
    try:
        with cls(connection) as client:
            state = client.fetch_state()
    except ServiceConnectionInvalid as exc:
        LOGGER.warning("Failed to get client status", exc=exc)
        return
    cache.set(connection.state_key, state, timeout=None)


@actor(description=_("Create/update/monitor/delete the deployment of an Outpost."))
def outpost_controller(outpost_pk: str, action: str = "up", from_cache: bool = False):
    """Create/update/monitor/delete the deployment of an Outpost"""
    self: Task = CurrentTask.get_task()
    self.set_uid(outpost_pk)
    logs = []
    if from_cache:
        outpost: Outpost = cache.get(CACHE_KEY_OUTPOST_DOWN % outpost_pk)
        LOGGER.debug("Getting outpost from cache to delete")
    else:
        outpost: Outpost = Outpost.objects.filter(pk=outpost_pk).first()
        LOGGER.debug("Getting outpost from DB")
    if not outpost:
        LOGGER.warning("No outpost")
        return
    self.set_uid(slugify(outpost.name))
    try:
        controller_type = controller_for_outpost(outpost)
        if not controller_type:
            return
        with controller_type(outpost, outpost.service_connection) as controller:
            LOGGER.debug("---------------Outpost Controller logs starting----------------")
            logs = getattr(controller, f"{action}_with_logs")()
            LOGGER.debug("-----------------Outpost Controller logs end-------------------")
    except (ControllerException, ServiceConnectionInvalid) as exc:
        self.error(exc)
    else:
        if from_cache:
            cache.delete(CACHE_KEY_OUTPOST_DOWN % outpost_pk)
        self.logs(logs)


@actor(description=_("Ensure that all Outposts have valid Service Accounts and Tokens."))
def outpost_token_ensurer():
    """
    Periodically ensure that all Outposts have valid Service Accounts and Tokens
    """
    self: Task = CurrentTask.get_task()
    all_outposts = Outpost.objects.all()
    for outpost in all_outposts:
        _ = outpost.token
        outpost.build_user_permissions(outpost.user)
    self.info(f"Successfully checked {len(all_outposts)} Outposts.")


@actor(description=_("Send update to outpost"))
def outpost_send_update(pk: Any):
    """Update outpost instance"""
    outpost = Outpost.objects.filter(pk=pk).first()
    if not outpost:
        return
    # Ensure token again, because this function is called when anything related to an
    # OutpostModel is saved, so we can be sure permissions are right
    _ = outpost.token
    outpost.build_user_permissions(outpost.user)
    layer = get_channel_layer()
    group = OUTPOST_GROUP % {"outpost_pk": str(outpost.pk)}
    LOGGER.debug("sending update", channel=group, outpost=outpost)
    async_to_sync(layer.group_send)(group, {"type": "event.update"})


@actor(description=_("Checks the local environment and create Service connections."))
def outpost_connection_discovery():
    """Checks the local environment and create Service connections."""
    self: Task = CurrentTask.get_task()
    if not CONFIG.get_bool("outposts.discover"):
        self.info("Outpost integration discovery is disabled")
        return
    # Explicitly check against token filename, as that's
    # only present when the integration is enabled
    if Path(SERVICE_TOKEN_FILENAME).exists():
        self.info("Detected in-cluster Kubernetes Config")
        if not KubernetesServiceConnection.objects.filter(local=True).exists():
            self.info("Created Service Connection for in-cluster")
            KubernetesServiceConnection.objects.create(
                name="Local Kubernetes Cluster", local=True, kubeconfig={}
            )
    # For development, check for the existence of a kubeconfig file
    kubeconfig_path = Path(KUBE_CONFIG_DEFAULT_LOCATION).expanduser()
    if kubeconfig_path.exists():
        self.info("Detected kubeconfig")
        kubeconfig_local_name = f"k8s-{gethostname()}"
        if not KubernetesServiceConnection.objects.filter(name=kubeconfig_local_name).exists():
            self.info("Creating kubeconfig Service Connection")
            with kubeconfig_path.open("r", encoding="utf8") as _kubeconfig:
                KubernetesServiceConnection.objects.create(
                    name=kubeconfig_local_name,
                    kubeconfig=safe_load(_kubeconfig),
                )
    unix_socket_path = urlparse(DEFAULT_UNIX_SOCKET).path
    socket = Path(unix_socket_path)
    if socket.exists() and access(socket, R_OK):
        self.info("Detected local docker socket")
        if len(DockerServiceConnection.objects.filter(local=True)) == 0:
            self.info("Created Service Connection for docker")
            DockerServiceConnection.objects.create(
                name="Local Docker connection",
                local=True,
                url=unix_socket_path,
            )


@actor(description=_("Terminate session on all outposts."))
def outpost_session_end(session_id: str):
    layer = get_channel_layer()
    hashed_session_id = hash_session_key(session_id)
    for outpost in Outpost.objects.all():
        LOGGER.info("Sending session end signal to outpost", outpost=outpost)
        group = OUTPOST_GROUP % {"outpost_pk": str(outpost.pk)}
        async_to_sync(layer.group_send)(
            group,
            {
                "type": "event.session.end",
                "session_id": hashed_session_id,
            },
        )
