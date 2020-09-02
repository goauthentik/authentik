"""outpost tasks"""
from passbook.outposts.controller.kubernetes import KubernetesController
from passbook.outposts.models import Outpost, OutpostDeploymentType
from passbook.root.celery import CELERY_APP


@CELERY_APP.task(bind=True)
# pylint: disable=unused-argument
def outpost_k8s_controller(self):
    """Launch Kubernetes Controller for all Outposts which are deployed in kubernetes"""
    for outpost in Outpost.objects.filter(
        deployment_type=OutpostDeploymentType.KUBERNETES
    ):
        outpost_k8s_controller_single.delay(outpost.pk.hex)


@CELERY_APP.task(bind=True)
# pylint: disable=unused-argument
def outpost_k8s_controller_single(self, outpost: str):
    """Launch Kubernetes manager and reconcile deployment/service/etc"""
    KubernetesController(outpost).run()
