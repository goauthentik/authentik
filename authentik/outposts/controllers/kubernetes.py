"""Kubernetes deployment controller"""
from io import StringIO

from kubernetes.client import VersionApi, VersionInfo
from kubernetes.client.api_client import ApiClient
from kubernetes.client.configuration import Configuration
from kubernetes.client.exceptions import OpenApiException
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.incluster_config import load_incluster_config
from kubernetes.config.kube_config import load_kube_config_from_dict
from structlog.testing import capture_logs
from urllib3.exceptions import HTTPError
from yaml import dump_all

from authentik.outposts.controllers.base import BaseClient, BaseController, ControllerException
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.deployment import DeploymentReconciler
from authentik.outposts.controllers.k8s.secret import SecretReconciler
from authentik.outposts.controllers.k8s.service import ServiceReconciler
from authentik.outposts.controllers.k8s.service_monitor import PrometheusServiceMonitorReconciler
from authentik.outposts.models import (
    KubernetesServiceConnection,
    Outpost,
    OutpostServiceConnectionState,
    ServiceConnectionInvalid,
)


class KubernetesClient(ApiClient, BaseClient):
    """Custom kubernetes client based on service connection"""

    def __init__(self, connection: KubernetesServiceConnection):
        config = Configuration()
        try:
            if connection.local:
                load_incluster_config(client_configuration=config)
            else:
                load_kube_config_from_dict(connection.kubeconfig, client_configuration=config)
            config.verify_ssl = connection.verify_ssl
            super().__init__(config)
        except ConfigException as exc:
            raise ServiceConnectionInvalid(exc) from exc

    def fetch_state(self) -> OutpostServiceConnectionState:
        """Get version info"""
        try:
            api_instance = VersionApi(self)
            version: VersionInfo = api_instance.get_code()
            return OutpostServiceConnectionState(version=version.git_version, healthy=True)
        except (OpenApiException, HTTPError, ServiceConnectionInvalid):
            return OutpostServiceConnectionState(version="", healthy=False)


class KubernetesController(BaseController):
    """Manage deployment of outpost in kubernetes"""

    reconcilers: dict[str, type[KubernetesObjectReconciler]]
    reconcile_order: list[str]

    client: KubernetesClient
    connection: KubernetesServiceConnection

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection) -> None:
        super().__init__(outpost, connection)
        self.client = KubernetesClient(connection)
        self.reconcilers = {
            SecretReconciler.reconciler_name(): SecretReconciler,
            DeploymentReconciler.reconciler_name(): DeploymentReconciler,
            ServiceReconciler.reconciler_name(): ServiceReconciler,
            PrometheusServiceMonitorReconciler.reconciler_name(): (
                PrometheusServiceMonitorReconciler
            ),
        }
        self.reconcile_order = [
            SecretReconciler.reconciler_name(),
            DeploymentReconciler.reconciler_name(),
            ServiceReconciler.reconciler_name(),
            PrometheusServiceMonitorReconciler.reconciler_name(),
        ]

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
