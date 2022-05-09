---
title: Overview
---

An outpost is a single deployment of a authentik component, which can be deployed in a completely separate environment. Currently, Proxy Provider and LDAP are supported as outposts.

![](outposts.png)

Upon creation, a service account and a token is generated. The service account only has permissions to read the outpost and provider configuration. This token is used by the Outpost to connect to authentik.

authentik can manage the deployment, updating and general lifecycle of an Outpost. To communicate with the underlying platforms on which the outpost is deployed, authentik has several built-in integrations.

-   If you've deployed authentik on docker-compose, authentik automatically creates an integration for the local docker socket (See [Docker](./integrations/docker.md)).
-   If you've deployed authentik on Kubernetes, with `kubernetesIntegration` set to true (default), authentik automatically creates an integrations for the local Kubernetes Cluster (See [Kubernetes](./integrations/kubernetes.md)).

To deploy an outpost with these integrations, simply select them during the creation of an Outpost. A background task is started, which creates the container/deployment. You can see that Status on the System Tasks page.

To deploy an outpost manually, see:

-   [Kubernetes](./manual-deploy-kubernetes.md)
-   [docker-compose](./manual-deploy-docker-compose.md)

## Configuration

Outposts fetch their configuration from authentik. Below are all the options you can set, and how they influence the outpost.

```yaml
# Log level that the outpost will set
# Allowed levels: trace, debug, info, warning, error
log_level: debug
########################################
# The settings below are only relevant when using a managed outpost
########################################
# URL that the outpost uses to connect back to authentik
authentik_host: https://authentik.tld/
# Disable SSL Validation for the authentik connection
authentik_host_insecure: false
# Optionally specify a different URL used for user-facing interactions
authentik_host_browser:
# Template used for objects created (deployments/containers, services, secrets, etc)
object_naming_template: ak-outpost-%(name)s
# Use a specific docker image for this outpost rather than the default. This also applies to Kubernetes
# outposts.
container_image:
########################################
# Docker outpost specific settings
########################################
# Network the outpost container should be connected to
docker_network: null
# Optionally disable mapping of ports to outpost container, may be useful when using docker networks
# (Available with 2021.9.4+)
docker_map_ports: true
# Optionally additional labels for docker containers
# (Available with 2022.1.2)
docker_labels: null
########################################
# Kubernetes outpost specific settings
########################################
# Replica count for the deployment of the outpost
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
kubernetes_image_pull_secrets: []
```

## Metrics

Each authentik outpost has a Prometheus metrics endpoint accessible under port `:9300/metrics`. This endpoint is not mapped via docker, as the endpoint doesn't have any authentication.

For the embedded outpost, the metrics of the outpost and the metrics of the core authentik server are both returned under the same endpoint.
