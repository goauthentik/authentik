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
    OutpostType,
)
from passbook.providers.proxy.controllers.docker import ProxyDockerController
from passbook.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True)
# pylint: disable=unused-argument
def outpost_controller(self):
    """Launch Controller for all Outposts which support it"""
    for outpost in Outpost.objects.exclude(
        deployment_type=OutpostDeploymentType.CUSTOM
    ):
        outpost_controller_single.delay(
            outpost.pk.hex, outpost.deployment_type, outpost.type
        )


@CELERY_APP.task(bind=True)
# pylint: disable=unused-argument
def outpost_controller_single(
    self, outpost: str, deployment_type: str, outpost_type: str
):
    """Launch controller and reconcile deployment/service/etc"""
    if outpost_type == OutpostType.PROXY:
        if deployment_type == OutpostDeploymentType.KUBERNETES:
            ProxyKubernetesController(outpost).run()
        if deployment_type == OutpostDeploymentType.DOCKER:
            ProxyDockerController(outpost).run()


@CELERY_APP.task()
def outpost_send_update(model_class: str, model_pk: Any):
    """Send outpost update to all registered outposts, irregardless to which passbook
    instance they are connected"""
    model = path_to_class(model_class)
    outpost_model: OutpostModel = model.objects.get(pk=model_pk)
    for outpost in outpost_model.outpost_set.all():
        channel_layer = get_channel_layer()
        for channel in outpost.channels:
            LOGGER.debug("sending update", channel=channel)
            async_to_sync(channel_layer.send)(channel, {"type": "event.update"})
