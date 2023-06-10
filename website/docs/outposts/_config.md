```yaml
# Log level that the outpost will set
# Allowed levels: trace, debug, info, warning, error
# Applies to: non-embedded
log_level: debug
########################################
# The settings below are only relevant when using a managed outpost
########################################
# URL that the outpost uses to connect back to authentik
authentik_host: https://authentik.tld/
# Disable SSL Validation for the authentik connection
authentik_host_insecure: false
# Optionally specify a different URL used for user-facing interactions
# Applies to: proxy outposts
authentik_host_browser:
# Template used for objects created (deployments/containers, services, secrets, etc)
object_naming_template: ak-outpost-%(name)s
# Use a specific docker image for this outpost rather than the default. This also applies to Kubernetes
# outposts.
# Applies to: non-embedded
container_image:
########################################
# Docker outpost specific settings
########################################
# Network the outpost container should be connected to
# Applies to: non-embedded
docker_network: null
# Optionally disable mapping of ports to outpost container, may be useful when using docker networks
# (Available with 2021.9.4+)
# Applies to: non-embedded
docker_map_ports: true
# Optionally additional labels for docker containers
# (Available with 2022.1.2)
# Applies to: non-embedded
docker_labels: null
########################################
# Kubernetes outpost specific settings
########################################
# Replica count for the deployment of the outpost
# Applies to: non-embedded
kubernetes_replicas: 1
# Namespace to deploy in, defaults to the same namespace authentik is deployed in (if available)
kubernetes_namespace: authentik
# Any additional annotations to add to the ingress object, for example cert-manager
kubernetes_ingress_annotations: {}
# Name of the secret that is used for TLS connections
kubernetes_ingress_secret_name: authentik-outpost-tls
# Service kind created, can be set to LoadBalancer for LDAP outposts for example
kubernetes_service_type: ClusterIP
# Disable any components of the kubernetes integration, can be any of
# - 'secret'
# - 'deployment'
# - 'service'
# - 'prometheus servicemonitor'
# - 'ingress'
# - 'traefik middleware'
kubernetes_disabled_components: []
# If the above docker image is in a private repository, use these secrets to pull.
# NOTE: The secret must be created manually in the namespace first.
# Applies to: non-embedded
kubernetes_image_pull_secrets: []
# Optionally configure an ingress class name. If not set, the ingress will use the cluster's
# default ingress class
# (Available with 2022.11.0+)
# Applies to: proxy outposts
kubernetes_ingress_class_name: null
# Optionally configure a Kubernetes affinity for outpost deployment
# Takes a single json string as input, E.G:
# '{"nodeAffinity":{"preferredDuringSchedulingIgnoredDuringExecution":[{"preference":{"matchExpressions":[{"key":"node-label-key","operator":"In","values":["node-label-value"]}]},"weight":1}],"requiredDuringSchedulingIgnoredDuringExecution":{"nodeSelectorTerms":[{"matchExpressions":[{"key":"topology.kubernetes.io/region","operator":"In","values":["east1"]},{"key":"topology.kubernetes.io/zone","operator":"In","values":["us-east-1c"]}]}]}}}'
kubernetes_affinity: null
# Optionally configure Kubernetes tolerations for outpost deployment
# Takes a single json string as input, E.G:
# '{"tolerations":[{"key":"is_cpu_compute","operator":"Exists"},{"key":"is_gpu_compute","operator":"Exists"}]}'
kubernetes_tolerations: null
# Optionally configure Kubernetes resources for outpost deployment
# Takes a single json string as input, E.G:
# '{"resources":{"requests":{"cpu":"2","memory":"4Gi"},"limits":{"cpu":"4","memory":"8Gi"}}}'
kubernetes_resources: null
```
