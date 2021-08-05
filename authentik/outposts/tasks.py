"""outpost tasks"""
from os import R_OK, access
from os.path import expanduser
from pathlib import Path
from socket import gethostname
from typing import Any, Optional
from urllib.parse import urlparse

import yaml
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models.base import Model
from django.utils.text import slugify
from docker.constants import DEFAULT_UNIX_SOCKET
from kubernetes.config.incluster_config import SERVICE_TOKEN_FILENAME
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION
from structlog.stdlib import get_logger

from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.utils.reflection import path_to_class
from authentik.outposts.controllers.base import BaseController, ControllerException
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
    OutpostModel,
    OutpostServiceConnection,
    OutpostState,
    OutpostType,
    ServiceConnectionInvalid,
)
from authentik.providers.ldap.controllers.docker import LDAPDockerController
from authentik.providers.ldap.controllers.kubernetes import LDAPKubernetesController
from authentik.providers.proxy.controllers.docker import ProxyDockerController
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()
CACHE_KEY_OUTPOST_DOWN = "outpost_teardown_%s"


def controller_for_outpost(outpost: Outpost) -> Optional[BaseController]:
    """Get a controller for the outpost, when a service connection is defined"""
    if not outpost.service_connection:
        return None
    service_connection = outpost.service_connection
    if outpost.type == OutpostType.PROXY:
        if isinstance(service_connection, DockerServiceConnection):
            return ProxyDockerController(outpost, service_connection)
        if isinstance(service_connection, KubernetesServiceConnection):
            return ProxyKubernetesController(outpost, service_connection)
    if outpost.type == OutpostType.LDAP:
        if isinstance(service_connection, DockerServiceConnection):
            return LDAPDockerController(outpost, service_connection)
        if isinstance(service_connection, KubernetesServiceConnection):
            return LDAPKubernetesController(outpost, service_connection)
    return None


@CELERY_APP.task()
def outpost_service_connection_state(connection_pk: Any):
    """Update cached state of a service connection"""
    connection: OutpostServiceConnection = (
        OutpostServiceConnection.objects.filter(pk=connection_pk).select_subclasses().first()
    )
    if not connection:
        return
    state = connection.fetch_state()
    cache.set(connection.state_key, state, timeout=None)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def outpost_service_connection_monitor(self: MonitoredTask):
    """Regularly check the state of Outpost Service Connections"""
    connections = OutpostServiceConnection.objects.all()
    for connection in connections.iterator():
        outpost_service_connection_state.delay(connection.pk)
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            [f"Successfully updated {len(connections)} connections."],
        )
    )


@CELERY_APP.task()
def outpost_controller_all():
    """Launch Controller for all Outposts which support it"""
    for outpost in Outpost.objects.exclude(service_connection=None):
        outpost_controller.delay(outpost.pk.hex, "up", from_cache=False)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def outpost_controller(
    self: MonitoredTask, outpost_pk: str, action: str = "up", from_cache: bool = False
):
    """Create/update/monitor/delete the deployment of an Outpost"""
    logs = []
    if from_cache:
        outpost: Outpost = cache.get(CACHE_KEY_OUTPOST_DOWN % outpost_pk)
    else:
        outpost: Outpost = Outpost.objects.get(pk=outpost_pk)
    if not outpost:
        return
    self.set_uid(slugify(outpost.name))
    try:
        controller = controller_for_outpost(outpost)
        if not controller:
            return
        logs = getattr(controller, f"{action}_with_logs")()
        LOGGER.debug("---------------Outpost Controller logs starting----------------")
        for log in logs:
            LOGGER.debug(log)
        LOGGER.debug("-----------------Outpost Controller logs end-------------------")
    except (ControllerException, ServiceConnectionInvalid) as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
    else:
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, logs))


@CELERY_APP.task(bind=True, base=MonitoredTask)
def outpost_token_ensurer(self: MonitoredTask):
    """Periodically ensure that all Outposts have valid Service Accounts
    and Tokens"""
    all_outposts = Outpost.objects.all()
    for outpost in all_outposts:
        _ = outpost.token
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            [f"Successfully checked {len(all_outposts)} Outposts."],
        )
    )


@CELERY_APP.task()
def outpost_post_save(model_class: str, model_pk: Any):
    """If an Outpost is saved, Ensure that token is created/updated

    If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    model: Model = path_to_class(model_class)
    try:
        instance = model.objects.get(pk=model_pk)
    except model.DoesNotExist:
        LOGGER.warning("Model does not exist", model=model, pk=model_pk)
        return

    if isinstance(instance, Outpost):
        LOGGER.debug("Ensuring token and permissions for outpost", instance=instance)
        _ = instance.token
        _ = instance.user
        LOGGER.debug("Trigger reconcile for outpost")
        outpost_controller.delay(instance.pk)

    if isinstance(instance, (OutpostModel, Outpost)):
        LOGGER.debug("triggering outpost update from outpostmodel/outpost", instance=instance)
        outpost_send_update(instance)

    if isinstance(instance, OutpostServiceConnection):
        LOGGER.debug("triggering ServiceConnection state update", instance=instance)
        outpost_service_connection_state.delay(instance.pk)

    for field in instance._meta.get_fields():
        # Each field is checked if it has a `related_model` attribute (when ForeginKeys or M2Ms)
        # are used, and if it has a value
        if not hasattr(field, "related_model"):
            continue
        if not field.related_model:
            continue
        if not issubclass(field.related_model, OutpostModel):
            continue

        field_name = f"{field.name}_set"
        if not hasattr(instance, field_name):
            continue

        LOGGER.debug("triggering outpost update from from field", field=field.name)
        # Because the Outpost Model has an M2M to Provider,
        # we have to iterate over the entire QS
        for reverse in getattr(instance, field_name).all():
            outpost_send_update(reverse)


def outpost_send_update(model_instace: Model):
    """Send outpost update to all registered outposts, irregardless to which authentik
    instance they are connected"""
    channel_layer = get_channel_layer()
    if isinstance(model_instace, OutpostModel):
        for outpost in model_instace.outpost_set.all():
            _outpost_single_update(outpost, channel_layer)
    elif isinstance(model_instace, Outpost):
        _outpost_single_update(model_instace, channel_layer)


def _outpost_single_update(outpost: Outpost, layer=None):
    """Update outpost instances connected to a single outpost"""
    # Ensure token again, because this function is called when anything related to an
    # OutpostModel is saved, so we can be sure permissions are right
    _ = outpost.token
    _ = outpost.user
    if not layer:  # pragma: no cover
        layer = get_channel_layer()
    for state in OutpostState.for_outpost(outpost):
        for channel in state.channel_ids:
            LOGGER.debug("sending update", channel=channel, instance=state.uid, outpost=outpost)
            async_to_sync(layer.send)(channel, {"type": "event.update"})


@CELERY_APP.task()
def outpost_local_connection():
    """Checks the local environment and create Service connections."""
    # Explicitly check against token filename, as thats
    # only present when the integration is enabled
    if Path(SERVICE_TOKEN_FILENAME).exists():
        LOGGER.debug("Detected in-cluster Kubernetes Config")
        if not KubernetesServiceConnection.objects.filter(local=True).exists():
            LOGGER.debug("Created Service Connection for in-cluster")
            KubernetesServiceConnection.objects.create(
                name="Local Kubernetes Cluster", local=True, kubeconfig={}
            )
    # For development, check for the existence of a kubeconfig file
    kubeconfig_path = expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
    if Path(kubeconfig_path).exists():
        LOGGER.debug("Detected kubeconfig")
        kubeconfig_local_name = f"k8s-{gethostname()}"
        if not KubernetesServiceConnection.objects.filter(name=kubeconfig_local_name).exists():
            LOGGER.debug("Creating kubeconfig Service Connection")
            with open(kubeconfig_path, "r") as _kubeconfig:
                KubernetesServiceConnection.objects.create(
                    name=kubeconfig_local_name,
                    kubeconfig=yaml.safe_load(_kubeconfig),
                )
    unix_socket_path = urlparse(DEFAULT_UNIX_SOCKET).path
    socket = Path(unix_socket_path)
    if socket.exists() and access(socket, R_OK):
        LOGGER.debug("Detected local docker socket")
        if len(DockerServiceConnection.objects.filter(local=True)) == 0:
            LOGGER.debug("Created Service Connection for docker")
            DockerServiceConnection.objects.create(
                name="Local Docker connection",
                local=True,
                url=unix_socket_path,
            )
