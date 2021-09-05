"""Kubernetes deployment controller"""
from io import StringIO
from typing import Type

from kubernetes.client.api_client import ApiClient
from kubernetes.client.exceptions import OpenApiException
from structlog.testing import capture_logs
from urllib3.exceptions import HTTPError
from yaml import dump_all

from authentik.outposts.controllers.base import BaseController, ControllerException
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.deployment import DeploymentReconciler
from authentik.outposts.controllers.k8s.secret import SecretReconciler
from authentik.outposts.controllers.k8s.service import ServiceReconciler
from authentik.outposts.models import KubernetesServiceConnection, Outpost, ServiceConnectionInvalid


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    reconcilers: dict[str, Type[KubernetesObjectReconciler]]
    reconcile_order: list[str]

    client: ApiClient
    connection: KubernetesServiceConnection

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection) -> None:
        super().__init__(outpost, connection)
        self.client = connection.client()
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

        except (OpenApiException, HTTPError, ServiceConnectionInvalid) as exc:
            raise ControllerException(str(exc)) from exc

    def up_with_logs(self) -> list[str]:
        try:
            all_logs = []
            for reconcile_key in self.reconcile_order:
                if reconcile_key in self.outpost.config.kubernetes_disabled_components:
                    all_logs += [f"{reconcile_key.title()}: Disabled"]
                    continue
                with capture_logs() as logs:
                    reconciler = self.reconcilers[reconcile_key](self)
                    reconciler.up()
                all_logs += [f"{reconcile_key.title()}: {x['event']}" for x in logs]
            return all_logs
        except (OpenApiException, HTTPError, ServiceConnectionInvalid) as exc:
            raise ControllerException(str(exc)) from exc

    def down(self):
        try:
            for reconcile_key in self.reconcile_order:
                reconciler = self.reconcilers[reconcile_key](self)
                self.logger.debug("Tearing down object", name=reconcile_key)
                reconciler.down()

        except (OpenApiException, HTTPError, ServiceConnectionInvalid) as exc:
            raise ControllerException(str(exc)) from exc

    def down_with_logs(self) -> list[str]:
        try:
            all_logs = []
            for reconcile_key in self.reconcile_order:
                if reconcile_key in self.outpost.config.kubernetes_disabled_components:
                    all_logs += [f"{reconcile_key.title()}: Disabled"]
                    continue
                with capture_logs() as logs:
                    reconciler = self.reconcilers[reconcile_key](self)
                    reconciler.down()
                all_logs += [f"{reconcile_key.title()}: {x['event']}" for x in logs]
            return all_logs
        except (OpenApiException, HTTPError, ServiceConnectionInvalid) as exc:
            raise ControllerException(str(exc)) from exc

    def get_static_deployment(self) -> str:
        documents = []
        for reconcile_key in self.reconcile_order:
            reconciler = self.reconcilers[reconcile_key](self)
            if reconciler.noop:
                continue
            documents.append(reconciler.get_reference_object().to_dict())

        with StringIO() as _str:
            dump_all(
                documents,
                stream=_str,
                default_flow_style=False,
            )
            return _str.getvalue()
