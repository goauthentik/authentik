"""Kubernetes deployment controller"""
from io import StringIO
from typing import Dict, List, Type

from kubernetes.client import OpenApiException
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.kube_config import load_kube_config_from_dict
from structlog.testing import capture_logs
from yaml import dump_all

from passbook.outposts.controllers.base import BaseController, ControllerException
from passbook.outposts.controllers.k8s.base import KubernetesObjectReconciler
from passbook.outposts.controllers.k8s.deployment import DeploymentReconciler
from passbook.outposts.controllers.k8s.secret import SecretReconciler
from passbook.outposts.controllers.k8s.service import ServiceReconciler
from passbook.outposts.models import KubernetesServiceConnection, Outpost


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    reconcilers: Dict[str, Type[KubernetesObjectReconciler]]
    reconcile_order: List[str]

    connection: KubernetesServiceConnection

    def __init__(
        self, outpost: Outpost, connection: KubernetesServiceConnection
    ) -> None:
        super().__init__(outpost, connection)
        try:
            if self.connection.local:
                load_incluster_config()
            else:
                load_kube_config_from_dict(self.connection.config)
        except ConfigException:
            load_kube_config()
        self.reconcilers = {
            "secret": SecretReconciler,
            "deployment": DeploymentReconciler,
            "service": ServiceReconciler,
        }
        self.reconcile_order = ["secret", "deployment", "service"]

    def up(self):
        try:
            for reconcile_key in self.reconcile_order:
                reconciler = self.reconcilers[reconcile_key](self)
                reconciler.up()

        except OpenApiException as exc:
            raise ControllerException from exc

    def up_with_logs(self) -> List[str]:
        try:
            all_logs = []
            for reconcile_key in self.reconcile_order:
                with capture_logs() as logs:
                    reconciler = self.reconcilers[reconcile_key](self)
                    reconciler.up()
                all_logs += [f"{reconcile_key.title()}: {x['event']}" for x in logs]
            return all_logs
        except OpenApiException as exc:
            raise ControllerException from exc

    def down(self):
        try:
            for reconcile_key in self.reconcile_order:
                reconciler = self.reconcilers[reconcile_key](self)
                reconciler.down()

        except OpenApiException as exc:
            raise ControllerException from exc

    def get_static_deployment(self) -> str:
        documents = []
        for reconcile_key in self.reconcile_order:
            reconciler = self.reconcilers[reconcile_key](self)
            documents.append(reconciler.get_reference_object().to_dict())

        with StringIO() as _str:
            dump_all(
                documents,
                stream=_str,
                default_flow_style=False,
            )
            return _str.getvalue()
