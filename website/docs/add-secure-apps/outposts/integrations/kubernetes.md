---
title: Kubernetes
---

The Kubernetes integration automatically deploys and manages outposts in a Kubernetes cluster.

Compared with a [manual Kubernetes deployment](../manual-deploy-kubernetes.md), this integration keeps managed outposts aligned with authentik updates and reduces the amount of cluster-side configuration that you need to maintain.

## Created resources

This integration creates the following Kubernetes resources:

- A `Deployment` for the outpost container.
- A `Service` for protocol traffic.
- A `Service` for metrics traffic.
- A `Secret` that stores the outpost token.
- A `ServiceMonitor` if the Prometheus Operator is installed in the target cluster.
- An `Ingress` for proxy outposts.
- An `HTTPRoute` for proxy outposts if Gateway API resources are installed in the target cluster and `kubernetes_httproute_parent_refs` is configured.
- A Traefik `Middleware` resource for proxy outposts that use forward auth.

## Supported settings

These settings control how authentik creates and manages Kubernetes resources. For the full shared outpost configuration reference, see [Outposts configuration](../index.mdx#configuration).

### General settings

- `object_naming_template`: Configures the names of created Kubernetes resources.
- `container_image`: Overrides the default outpost image. You can also configure the global default in [Configuration](../../../install-config/configuration/configuration.mdx#authentik_outposts).
- `kubernetes_replicas`: Sets the number of replicas in the generated deployment.
- `kubernetes_namespace`: Sets the namespace where authentik deploys the outpost. By default, this uses the namespace where authentik is installed, if available.
- `kubernetes_service_type`: Sets the generated Service type, for example `ClusterIP` or `LoadBalancer`.
- `kubernetes_image_pull_secrets`: Uses existing image pull secrets for private registries. Create these secrets in the target namespace before you use this setting.
- `kubernetes_json_patches`: Applies [RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902) JSON patches to generated Kubernetes objects.
- `kubernetes_disable_x509_strict`: Disable strict X.509 validation for the Kubernetes integration. Enable this setting if your cluster's root CA certificate was generated without certain key usage extensions. Seeing `certificate verify failed` errors in the outpost logs is an indicator that this setting should be set to `true`.

### Ingress settings

- `kubernetes_ingress_annotations`: Adds annotations to the generated Ingress, for example for cert-manager.
- `kubernetes_ingress_secret_name`: Sets the TLS secret name for the generated Ingress. Leave this empty to disable TLS configuration on the Ingress.
- `kubernetes_ingress_class_name`: Sets the ingress class for the generated Ingress.
- `kubernetes_ingress_path_type`: Sets the Ingress `pathType`. If unset, authentik uses the controller default.

### Gateway API settings

- `kubernetes_httproute_parent_refs`: Defines which Gateway resources the generated `HTTPRoute` attaches to.
- `kubernetes_httproute_annotations`: Adds annotations to the generated `HTTPRoute`.

### Disabled components

Use `kubernetes_disabled_components` to prevent authentik from creating specific resources. Supported values are:

- `secret`
- `deployment`
- `service`
- `service-metrics`
- `prometheus servicemonitor`
- `ingress`
- `traefik middleware`
- `httproute`

## Permissions

The required permissions for this integration are documented in the Helm chart:

- [Cluster-level permissions](https://github.com/goauthentik/helm/blob/main/charts/authentik-remote-cluster/templates/clusterrolebinding.yaml)
- [Namespace-level permissions](https://github.com/goauthentik/helm/blob/main/charts/authentik-remote-cluster/templates/rolebinding.yaml)

## Remote clusters

To connect a remote cluster, install the [`authentik-remote-cluster` Helm chart](https://artifacthub.io/packages/helm/goauthentik/authentik-remote-cluster) in the target cluster and namespace.

After installation, the chart outputs an example kubeconfig file. Add that kubeconfig to authentik to connect to the cluster.
