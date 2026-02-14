"""Kubernetes Deployment Reconciler"""

from typing import TYPE_CHECKING

from django.utils.text import slugify
from base64 import b64decode

from kubernetes.client import (
    AppsV1Api,
    CoreV1Api,
    V1Capabilities,
    V1Container,
    V1ContainerPort,
    V1Deployment,
    V1DeploymentSpec,
    V1EnvFromSource,
    V1EnvVar,
    V1EnvVarSource,
    V1LabelSelector,
    V1ObjectMeta,
    V1ObjectReference,
    V1PodSecurityContext,
    V1PodSpec,
    V1PodTemplateSpec,
    V1SeccompProfile,
    V1SecretEnvSource,
    V1SecretKeySelector,
    V1SecurityContext,
    V1Volume,
    V1VolumeMount,
    V1SecretVolumeSource,
)

from authentik import authentik_full_version
from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.k8s.utils import compare_ports
from authentik.outposts.models import Outpost

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


# PostgreSQL environment variable names that may contain file:// references
POSTGRESQL_ENV_VARS = [
    "AUTHENTIK_POSTGRESQL__USER",
    "AUTHENTIK_POSTGRESQL__PASSWORD",
    "AUTHENTIK_POSTGRESQL__NAME",
    "AUTHENTIK_POSTGRESQL__HOST",
]


class DeploymentReconciler(KubernetesObjectReconciler[V1Deployment]):
    """Kubernetes Deployment Reconciler"""

    outpost: Outpost

    def __init__(self, controller: KubernetesController) -> None:
        super().__init__(controller)
        self.api = AppsV1Api(controller.client)
        self.outpost = self.controller.outpost

    @property
    def noop(self) -> bool:
        return self.is_embedded

    @staticmethod
    def reconciler_name() -> str:
        return "deployment"

    def reconcile(self, current: V1Deployment, reference: V1Deployment):
        compare_ports(
            current.spec.template.spec.containers[0].ports,
            reference.spec.template.spec.containers[0].ports,
        )
        if current.spec.replicas != reference.spec.replicas:
            raise NeedsUpdate()
        if (
            current.spec.template.spec.containers[0].image
            != reference.spec.template.spec.containers[0].image
        ):
            raise NeedsUpdate()
        # Check if envFrom changed (for PostgreSQL secret injection)
        if (
            current.spec.template.spec.containers[0].env_from
            != reference.spec.template.spec.containers[0].env_from
        ):
            raise NeedsUpdate()
        # Check if volumes changed (for PostgreSQL credentials mount)
        if current.spec.template.spec.volumes != reference.spec.template.spec.volumes:
            raise NeedsUpdate()
        # Check if volume mounts changed
        if (
            current.spec.template.spec.containers[0].volume_mounts
            != reference.spec.template.spec.containers[0].volume_mounts
        ):
            raise NeedsUpdate()
        super().reconcile(current, reference)

    def get_pod_meta(self, **kwargs) -> dict[str, str]:
        """Get common object metadata"""
        kwargs.update(
            {
                "app.kubernetes.io/name": f"authentik-outpost-{self.outpost.type}",
                "app.kubernetes.io/managed-by": "goauthentik.io",
                "goauthentik.io/outpost-uuid": self.controller.outpost.uuid.hex,
                "goauthentik.io/outpost-name": slugify(self.controller.outpost.name),
                "goauthentik.io/outpost-type": str(self.controller.outpost.type),
            }
        )
        return kwargs

    def get_reference_object(self) -> V1Deployment:
        """Get deployment object for outpost"""
        # Generate V1ContainerPort objects
        container_ports = []
        for port in self.controller.deployment_ports:
            container_ports.append(
                V1ContainerPort(
                    container_port=port.inner_port or port.port,
                    name=port.name,
                    protocol=port.protocol.upper(),
                )
            )
        meta = self.get_object_meta(name=self.name)
        image_name = self.controller.get_container_image()
        image_pull_secrets = self.outpost.config.kubernetes_image_pull_secrets
        version = authentik_full_version().replace("+", "-")
        return V1Deployment(
            metadata=meta,
            spec=V1DeploymentSpec(
                replicas=self.outpost.config.kubernetes_replicas,
                selector=V1LabelSelector(match_labels=self.get_pod_meta()),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(
                        labels=self.get_pod_meta(
                            **{
                                # Support istio-specific labels, but also use the standard k8s
                                # recommendations
                                "app.kubernetes.io/version": version,
                                "app": "authentik-outpost",
                                "version": version,
                            }
                        )
                    ),
                    spec=V1PodSpec(
                        image_pull_secrets=[
                            V1ObjectReference(name=secret) for secret in image_pull_secrets
                        ],
                        security_context=V1PodSecurityContext(
                            seccomp_profile=V1SeccompProfile(
                                type="RuntimeDefault",
                            ),
                        ),
                        volumes=self._get_volumes(),
                        containers=[
                            V1Container(
                                name=str(self.outpost.type),
                                image=image_name,
                                ports=container_ports,
                                volume_mounts=self._get_volume_mounts(),
                                env=[
                                    V1EnvVar(
                                        name="AUTHENTIK_HOST",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=self.name,
                                                key="authentik_host",
                                            )
                                        ),
                                    ),
                                    V1EnvVar(
                                        name="AUTHENTIK_HOST_BROWSER",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=self.name,
                                                key="authentik_host_browser",
                                            )
                                        ),
                                    ),
                                    V1EnvVar(
                                        name="AUTHENTIK_TOKEN",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=self.name,
                                                key="token",
                                            )
                                        ),
                                    ),
                                    V1EnvVar(
                                        name="AUTHENTIK_INSECURE",
                                        value_from=V1EnvVarSource(
                                            secret_key_ref=V1SecretKeySelector(
                                                name=self.name,
                                                key="authentik_host_insecure",
                                            )
                                        ),
                                    ),
                                ],
                                env_from=self._get_env_from_sources(),
                                security_context=V1SecurityContext(
                                    run_as_non_root=True,
                                    allow_privilege_escalation=False,
                                    capabilities=V1Capabilities(
                                        drop=["ALL"],
                                    ),
                                ),
                            )
                        ],
                    ),
                ),
            ),
        )

    def _needs_postgresql_credentials(self) -> bool:
        """Check if this outpost needs PostgreSQL credentials injected"""
        session_backend = self.outpost.config.session_backend.lower()
        return session_backend in ("postgres", "postgresql")

    def _secret_contains_file_references(self, secret_name: str) -> tuple[bool, str, str, str]:
        """Check if a secret contains file:// URI references in PostgreSQL env vars.
        Returns (has_file_refs, credentials_secret_name, volume_mount_path, volume_name)
        """
        try:
            core_api = CoreV1Api(api_client=self.api.api_client)
            secret = core_api.read_namespaced_secret(secret_name, self.namespace)
            
            if not secret.data:
                self.logger.warning(
                    "Secret has no data",
                    outpost=self.outpost.name,
                    secret_name=secret_name,
                )
                return False, "", "", ""
            
            # Check PostgreSQL-related env vars for file:// references
            credentials_secret = ""
            mount_path = ""
            volume_name = ""
            has_file_refs = False
            
            for var_name in POSTGRESQL_ENV_VARS:
                if var_name in secret.data:
                    # Decode base64 value
                    value = b64decode(secret.data[var_name]).decode('utf-8')
                    
                    if value.startswith("file://"):
                        has_file_refs = True
                        
                        # Extract mount path from file:///postgres-creds/username -> /postgres-creds
                        if not mount_path:
                            file_path = value.replace("file://", "")
                            # Get directory part: /postgres-creds/username -> /postgres-creds
                            mount_path = "/" + file_path.lstrip("/").split("/")[0]
                            # Volume name is mount path without leading slash
                            volume_name = mount_path.lstrip("/")
                        
                        self.logger.debug(
                            "Detected file:// reference",
                            outpost=self.outpost.name,
                            var_name=var_name,
                            mount_path=mount_path,
                        )
                        
                        # Try to infer the credentials secret name
                        if not credentials_secret:
                            # First check if kubernetes_postgresql_credentials_secret_name is configured
                            credentials_secret = self.outpost.config.kubernetes_postgresql_credentials_secret_name
                            if credentials_secret:
                                self.logger.debug(
                                    "Using configured credentials secret",
                                    outpost=self.outpost.name,
                                    credentials_secret=credentials_secret,
                                )
            
            if has_file_refs and not credentials_secret:
                # Try to find the credentials secret by examining secrets in namespace
                # Look for secrets with typical credential keys (username, password, database)
                try:
                    secrets_list = core_api.list_namespaced_secret(self.namespace)
                    
                    for secret in secrets_list.items:
                        if not secret.data:
                            continue
                        
                        # Check if secret has typical PostgreSQL credential keys
                        keys = set(secret.data.keys())
                        required_keys = {"username", "password", "database"}
                        
                        # If secret contains all required credential keys, it's likely the credentials secret
                        if required_keys.issubset(keys):
                            credentials_secret = secret.metadata.name
                            self.logger.debug(
                                "Auto-detected credentials secret",
                                outpost=self.outpost.name,
                                credentials_secret=credentials_secret,
                            )
                            break
                except Exception as e:
                    self.logger.debug(
                        "Failed to auto-detect credentials secret",
                        outpost=self.outpost.name,
                        error=str(e),
                    )
            
            return has_file_refs, credentials_secret, mount_path, volume_name
            
        except Exception as e:
            self.logger.warning(
                "Failed to read secret for file:// detection",
                outpost=self.outpost.name,
                secret_name=secret_name,
                error=str(e),
            )
            return False, "", "", ""

    def _get_env_from_sources(self) -> list[V1EnvFromSource]:
        """Get envFrom sources for the container, including PostgreSQL secret if needed"""
        env_from = []
        
        if self._needs_postgresql_credentials():
            secret_name = self.outpost.config.kubernetes_postgresql_secret_name
            
            if not secret_name:
                self.logger.warning(
                    "session_backend is set to postgres but kubernetes_postgresql_secret_name is empty",
                    outpost=self.outpost.name,
                )
                return env_from
            
            env_from.append(
                V1EnvFromSource(
                    secret_ref=V1SecretEnvSource(name=secret_name)
                )
            )
            
            self.logger.debug(
                "PostgreSQL envFrom configured",
                outpost=self.outpost.name,
                secret_name=secret_name,
            )
        
        return env_from

    def _get_volume_mounts(self) -> list[V1VolumeMount]:
        """Get volume mounts for the container, including PostgreSQL credentials if needed"""
        volume_mounts = []
        
        if self._needs_postgresql_credentials():
            secret_name = self.outpost.config.kubernetes_postgresql_secret_name
            
            if secret_name:
                # Check if the secret contains file:// references
                has_file_refs, creds_secret, mount_path, volume_name = self._secret_contains_file_references(secret_name)
                
                if has_file_refs and creds_secret and mount_path and volume_name:
                    volume_mounts.append(
                        V1VolumeMount(
                            name=volume_name,
                            mount_path=mount_path,
                            read_only=True,
                        )
                    )
                    
                    self.logger.debug(
                        "PostgreSQL volume mount configured",
                        outpost=self.outpost.name,
                        mount_path=mount_path,
                        credentials_secret=creds_secret,
                    )
                elif has_file_refs:
                    self.logger.warning(
                        "Secret contains file:// references but credentials secret not found. "
                        "Set kubernetes_postgresql_credentials_secret_name in config.",
                        outpost=self.outpost.name,
                    )
        
        return volume_mounts

    def _get_volumes(self) -> list[V1Volume]:
        """Get volumes for the pod spec, including PostgreSQL credentials if needed"""
        volumes = []
        
        if self._needs_postgresql_credentials():
            secret_name = self.outpost.config.kubernetes_postgresql_secret_name
            
            if secret_name:
                # Check if the secret contains file:// references
                has_file_refs, creds_secret, mount_path, volume_name = self._secret_contains_file_references(secret_name)
                
                if has_file_refs and creds_secret and volume_name:
                    volumes.append(
                        V1Volume(
                            name=volume_name,
                            secret=V1SecretVolumeSource(
                                secret_name=creds_secret,
                            ),
                        )
                    )
                    
                    self.logger.debug(
                        "PostgreSQL volume configured",
                        outpost=self.outpost.name,
                        volume_name=volume_name,
                        credentials_secret=creds_secret,
                    )
        
        return volumes

    def create(self, reference: V1Deployment):
        return self.api.create_namespaced_deployment(
            self.namespace, reference, field_manager=FIELD_MANAGER
        )

    def delete(self, reference: V1Deployment):
        return self.api.delete_namespaced_deployment(reference.metadata.name, self.namespace)

    def retrieve(self) -> V1Deployment:
        return self.api.read_namespaced_deployment(self.name, self.namespace)

    def update(self, current: V1Deployment, reference: V1Deployment):
        return self.api.patch_namespaced_deployment(
            current.metadata.name,
            self.namespace,
            reference,
            field_manager=FIELD_MANAGER,
        )
