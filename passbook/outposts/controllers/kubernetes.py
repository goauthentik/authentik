"""Kubernetes deployment controller"""
from io import StringIO

from kubernetes.client import OpenApiException
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from yaml import dump_all

from passbook.outposts.controllers.base import BaseController, ControllerException
from passbook.outposts.controllers.k8s.deployment import DeploymentReconciler
from passbook.outposts.controllers.k8s.secret import SecretReconciler
from passbook.outposts.controllers.k8s.service import ServiceReconciler


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    def __init__(self, outpost_pk: str) -> None:
        super().__init__(outpost_pk)
        try:
            load_incluster_config()
        except ConfigException:
            load_kube_config()

    def run(self):
        """Called by scheduled task to reconcile deployment/service/etc"""
        try:
            namespace = self.outpost.config.kubernetes_namespace

            secret_reconciler = SecretReconciler(self.outpost)
            secret_reconciler.namespace = namespace
            secret_reconciler.run()

            deployment_reconciler = DeploymentReconciler(self.outpost)
            deployment_reconciler.namespace = namespace
            deployment_reconciler.deployment_ports = self.deployment_ports
            deployment_reconciler.run()

            service_reconciler = ServiceReconciler(self.outpost)
            service_reconciler.namespace = namespace
            service_reconciler.deployment_ports = self.deployment_ports
            service_reconciler.run()
        except OpenApiException as exc:
            raise ControllerException from exc

    def get_static_deployment(self) -> str:
        secret_reconciler = SecretReconciler(self.outpost)
        secret_reconciler.namespace = ""

        deployment_reconciler = DeploymentReconciler(self.outpost)
        deployment_reconciler.namespace = ""
        deployment_reconciler.deployment_ports = self.deployment_ports

        service_reconciler = ServiceReconciler(self.outpost)
        service_reconciler.namespace = ""
        service_reconciler.deployment_ports = self.deployment_ports
        with StringIO() as _str:
            dump_all(
                [
                    secret_reconciler.get_reference_object().to_dict(),
                    deployment_reconciler.get_reference_object().to_dict(),
                    service_reconciler.get_reference_object().to_dict(),
                ],
                stream=_str,
                default_flow_style=False,
            )
            return _str.getvalue()
