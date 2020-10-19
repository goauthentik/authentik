"""Kubernetes deployment controller"""
from io import StringIO
from typing import Dict, List, Type

from kubernetes.client import OpenApiException
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from yaml import dump_all

from passbook.outposts.controllers.base import BaseController, ControllerException
from passbook.outposts.controllers.k8s.base import KubernetesObjectReconciler
from passbook.outposts.controllers.k8s.deployment import DeploymentReconciler
from passbook.outposts.controllers.k8s.secret import SecretReconciler
from passbook.outposts.controllers.k8s.service import ServiceReconciler
from passbook.outposts.models import Outpost


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    reconcilers: Dict[str, Type[KubernetesObjectReconciler]]
    reconcile_order: List[str]

    def __init__(self, outpost: Outpost) -> None:
        super().__init__(outpost)
        try:
            load_incluster_config()
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
