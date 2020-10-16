"""outpost tasks"""
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.base import Model
from structlog import get_logger

from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.lib.utils.reflection import path_to_class
from passbook.outposts.controllers.base import ControllerException
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
def outpost_controller_all():
    """Launch Controller for all Outposts which support it"""
    for outpost in Outpost.objects.exclude(
        deployment_type=OutpostDeploymentType.CUSTOM
    ):
        outpost_controller.delay(outpost.pk.hex, outpost.deployment_type, outpost.type)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def outpost_controller(
    self: MonitoredTask, outpost_pk: str, deployment_type: str, outpost_type: str
):
    """Launch controller and reconcile deployment/service/etc"""
    logs = []
    try:
        if outpost_type == OutpostType.PROXY:
            if deployment_type == OutpostDeploymentType.KUBERNETES:
                logs = ProxyKubernetesController(outpost_pk).run_with_logs()
            if deployment_type == OutpostDeploymentType.DOCKER:
                logs = ProxyDockerController(outpost_pk).run_with_logs()
    except ControllerException as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR, [str(exc)], exc))
    else:
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, logs))


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
        LOGGER.debug("Ensuring token for outpost", instance=instance)
        _ = instance.token
        return

    if isinstance(instance, (OutpostModel, Outpost)):
        LOGGER.debug(
            "triggering outpost update from outpostmodel/outpost", instance=instance
        )
        outpost_send_update(instance)
        return

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
    """Send outpost update to all registered outposts, irregardless to which passbook
    instance they are connected"""
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
