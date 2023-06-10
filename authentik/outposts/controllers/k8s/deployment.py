"""Kubernetes Deployment Reconciler"""
from json import JSONDecodeError, loads
from typing import TYPE_CHECKING

from django.utils.text import slugify
from kubernetes.client import (
    AppsV1Api,
    V1Affinity,
    V1Capabilities,
    V1Container,
    V1ContainerPort,
    V1Deployment,
    V1DeploymentSpec,
    V1EnvVar,
    V1EnvVarSource,
    V1LabelSelector,
    V1NodeAffinity,
    V1NodeSelectorRequirement,
    V1NodeSelectorTerm,
    V1NodeSelector,
    V1ObjectMeta,
    V1ObjectReference,
    V1PodSecurityContext,
    V1PodSpec,
    V1PodTemplateSpec,
    V1PreferredSchedulingTerm,
    V1ResourceRequirements,
    V1SeccompProfile,
    V1SecretKeySelector,
    V1SecurityContext,
    V1Toleration,
)

from authentik import get_full_version
from authentik.outposts.controllers.base import FIELD_MANAGER
from authentik.outposts.controllers.k8s.base import KubernetesObjectReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.controllers.k8s.utils import compare_ports
from authentik.outposts.models import Outpost

if TYPE_CHECKING:
    from authentik.outposts.controllers.kubernetes import KubernetesController


class DeploymentReconciler(KubernetesObjectReconciler[V1Deployment]):
    """Kubernetes Deployment Reconciler"""

    outpost: Outpost

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api = AppsV1Api(controller.client)
        self.outpost = self.controller.outpost

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

    def construct_resources(self, json_input):
        if json_input is None:
            return None

        try:
            data = loads(json_input)
        except JSONDecodeError:
            print("Error: Invalid JSON input")
            return None

        resources_data = data.get("resources", {})
        requests = resources_data.get("requests", {})
        limits = resources_data.get("limits", {})
        resource_requirements = V1ResourceRequirements(limits=limits, requests=requests)
        return resource_requirements

    def construct_tolerations(self, json_input):
        if json_input is None:
            return None

        try:
            data = loads(json_input)
        except JSONDecodeError:
            print("Error: Invalid JSON input")
            return None

        tolerations_data = data.get("tolerations", [])
        tolerations = []
        for toleration_data in tolerations_data:
            key = toleration_data.get("key")
            operator = toleration_data.get("operator")
            if key and operator:
                toleration = V1Toleration(key=key, operator=operator)
                tolerations.append(toleration)
        return tolerations

    def construct_affinity(self, json_input):
        if json_input is None:
            return None

        try:
            data = loads(json_input)
        except JSONDecodeError:
            print("Error: Invalid JSON input")
            return None

        node_affinity_data = data.get("nodeAffinity", {})
        preferred_during_scheduling = node_affinity_data.get(
            "preferredDuringSchedulingIgnoredDuringExecution", []
        )
        required_during_scheduling = node_affinity_data.get(
            "requiredDuringSchedulingIgnoredDuringExecution", {}
        )
        affinity = V1Affinity()
        affinity.node_affinity = V1NodeAffinity()

        if preferred_during_scheduling:
            preferred_during_scheduling_affinity = []
            for preference in preferred_during_scheduling:
                preference_data = preference.get("preference", {})
                match_expressions = preference_data.get("matchExpressions", [])
                match_expressions_list = []
                for expression in match_expressions:
                    key = expression.get("key")
                    operator = expression.get("operator")
                    values = expression.get("values")
                    if key is not None and operator is not None and values is not None:
                        match_expressions_list.append(
                            V1NodeSelectorRequirement(key=key, operator=operator, values=values)
                        )
                    else:
                        print("Error: Invalid match expression")
                preferred_during_scheduling_affinity.append(
                    V1PreferredSchedulingTerm(
                        preference=V1NodeSelectorTerm(match_expressions=match_expressions_list),
                        weight=preference.get("weight"),
                    )
                )

            affinity.node_affinity.preferred_during_scheduling_ignored_during_execution = (
                preferred_during_scheduling_affinity
            )

        if required_during_scheduling:
            node_selector_terms = required_during_scheduling.get("nodeSelectorTerms", [])
            if node_selector_terms:
                required_match_expressions = node_selector_terms[0].get("matchExpressions", [])
                required_match_expressions_list = []
                for expression in required_match_expressions:
                    key = expression.get("key")
                    operator = expression.get("operator")
                    values = expression.get("values")
                    if key is not None and operator is not None and values is not None:
                        required_match_expressions_list.append(
                            V1NodeSelectorRequirement(key=key, operator=operator, values=values)
                        )
                    else:
                        print("Error: Invalid match expression")
                affinity.node_affinity.required_during_scheduling_ignored_during_execution = V1NodeSelector(
                    node_selector_terms=[V1NodeSelectorTerm(match_expressions=required_match_expressions_list)]
                )
            else:
                print("Error: No nodeSelectorTerms found")

        return affinity

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
        version = get_full_version()
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
                        affinity=self.construct_affinity(self.outpost.config.kubernetes_affinity),
                        tolerations=self.construct_tolerations(
                            self.outpost.config.kubernetes_tolerations
                        ),
                        image_pull_secrets=[
                            V1ObjectReference(name=secret) for secret in image_pull_secrets
                        ],
                        security_context=V1PodSecurityContext(
                            seccomp_profile=V1SeccompProfile(
                                type="RuntimeDefault",
                            ),
                        ),
                        containers=[
                            V1Container(
                                name=str(self.outpost.type),
                                image=image_name,
                                ports=container_ports,
                                resources=self.construct_resources(
                                    self.outpost.config.kubernetes_resources
                                ),
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
