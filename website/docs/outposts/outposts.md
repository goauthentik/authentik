---
title: Outposts
---

An outpost is a single deployment of a authentik component, which can be deployed in a completely separate environment. Currently, only the Proxy Provider is supported as outpost.

![](outposts.png)

Upon creation, a service account and a token is generated. The service account only has permissions to read the outpost and provider configuration. This token is used by the Outpost to connect to authentik.

authentik can manage the deployment, updating and general lifecycle of an Outpost. To communicate with the underlying platforms on which the outpost is deployed, authentik has "Service Connections".

- If you've deployed authentik on docker-compose, authentik automatically create a Service Connection for the local docker socket.
- If you've deployed authentik on Kubernetes, with `kubernetesIntegration` set to true (default), authentik automatically creates a Service Connection for the local Kubernetes Cluster.

To deploy an outpost with these service connections, simply selected them during the creation of an Outpost. A background task is started, which creates the container/deployment. You can see that Status on the System Tasks page.

To deploy an outpost manually, see:

- [Kubernetes](./manual-deploy-kubernetes.md)
- [docker-compose](./manual-deploy-docker-compose.md)

## Configuration

Outposts fetch their configuration from authentik. Below are all the options you can set, and how they influence the outpost.

```yaml
# Log level that the outpost will set
log_level: debug
# Enable/disable error reporting for the outpost, based on the authentik settings
error_reporting_enabled: true
error_reporting_environment: beryjuorg-prod
########################################
# The settings below are only relevant when using a managed outpost
########################################
# URL that the outpost uses to connect back to authentik
authentik_host: https://authentik.tld/
# Disable SSL Validation for the authentik connection
authentik_host_insecure: false
# Template used for objects created (deployments, services, secrets, etc)
object_naming_template: ak-outpost-%(name)s
########################################
# Kubernetes outpost specific settings
########################################
# Network the outpost container should be connected to
docker_network: null
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
# - 'ingress'
# - 'traefik middleware'
kubernetes_disabled_components: []
```
