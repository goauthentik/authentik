"""outpost tasks"""
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from structlog import get_logger

from passbook.lib.utils.reflection import path_to_class
from passbook.outposts.models import (
    Outpost,
    OutpostDeploymentType,
    OutpostModel,
    OutpostState,
    OutpostType,
)
from passbook.providers.proxy.controllers.docker import ProxyDockerController
from passbook.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def outpost_controller():
    """Launch Controller for all Outposts which support it"""
    for outpost in Outpost.objects.exclude(
        deployment_type=OutpostDeploymentType.CUSTOM
    ):
        outpost_controller_single.delay(
            outpost.pk.hex, outpost.deployment_type, outpost.type
        )


@CELERY_APP.task()
def outpost_controller_single(outpost_pk: str, deployment_type: str, outpost_type: str):
    """Launch controller and reconcile deployment/service/etc"""
    if outpost_type == OutpostType.PROXY:
        if deployment_type == OutpostDeploymentType.KUBERNETES:
            ProxyKubernetesController(outpost_pk).run()
        if deployment_type == OutpostDeploymentType.DOCKER:
            ProxyDockerController(outpost_pk).run()


@CELERY_APP.task()
def outpost_send_update(model_class: str, model_pk: Any):
    """Send outpost update to all registered outposts, irregardless to which passbook
    instance they are connected"""
    model = path_to_class(model_class)
    model_instace = model.objects.get(pk=model_pk)
    channel_layer = get_channel_layer()
    if isinstance(model_instace, OutpostModel):
        for outpost in model_instace.outpost_set.all():
            _outpost_single_update(outpost, channel_layer)
    elif isinstance(model_instace, Outpost):
        _outpost_single_update(model_instace, channel_layer)


def _outpost_single_update(outpost: Outpost, layer=None):
    """Update outpost instances connected to a single outpost"""
    if not layer:  # pragma: no cover
        layer = get_channel_layer()
    for state in OutpostState.for_outpost(outpost):
        LOGGER.debug("sending update", channel=state.uid, outpost=outpost)
        async_to_sync(layer.send)(state.uid, {"type": "event.update"})
