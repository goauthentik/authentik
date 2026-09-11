<p align="center">
    <img src="https://goauthentik.io/img/icon_top_brand_colour.svg" height="150" alt="authentik logo">
</p>

---

[![Join Discord](https://img.shields.io/discord/809154715984199690?label=Discord&style=for-the-badge)](https://goauthentik.io/discord)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/goauthentik/helm/lint-test.yaml?branch=main&label=ci&style=for-the-badge)](https://github.com/goauthentik/helm/actions/workflows/lint-test.yaml)
![Version: 2026.8.0](https://img.shields.io/badge/Version-2026.8.0-informational?style=flat-square)
![AppVersion: 2026.8.0](https://img.shields.io/badge/AppVersion-2026.8.0-informational?style=flat-square)

authentik is an open-source Identity Provider focused on flexibility and versatility

**Homepage:** <https://goauthentik.io>

## Example values to get started:

```yaml
authentik:
  secret_key: "PleaseGenerateA50CharKey"
  # This sends anonymous usage-data, stack traces on errors and
  # performance data to authentik.error-reporting.a7k.io, and is fully opt-in
  error_reporting:
    enabled: true
  postgresql:
    password: "ThisIsNotASecurePassword"

server:
  ingress:
    enabled: true
    hosts:
      - authentik.domain.tld

postgresql:
  enabled: true
  auth:
    password: "ThisIsNotASecurePassword"
```

## Setting the authentik version

> [!WARNING]
> This should only be used to adjust the patch version of authentik as newer chart versions might require a matching authentik version.

```yaml
global:
  image:
    tag: 2025.12.4
```

## Advanced values examples

<details>
<summary>External PostgreSQL</summary>

```yaml
authentik:
  postgresql:
    host: postgres.domain.tld
    user: file:///postgres-creds/username
    password: file:///postgres-creds/password
server:
  volumes:
    - name: postgres-creds
      secret:
        secretName: authentik-postgres-credentials
  volumeMounts:
    - name: postgres-creds
      mountPath: /postgres-creds
      readOnly: true
worker:
  volumes:
    - name: postgres-creds
      secret:
        secretName: authentik-postgres-credentials
  volumeMounts:
    - name: postgres-creds
      mountPath: /postgres-creds
      readOnly: true
```

The secret `authentik-postgres-credentials` must have `username` and `password` keys.
</details>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| authentik Team | <hello@goauthentik.io> | <https://goauthentik.io> |

## Source Code

* <https://goauthentik.io/docs/>
* <https://github.com/goauthentik/authentik>

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://charts.goauthentik.io | serviceAccount(authentik-remote-cluster) | 2.1.0 |
| oci://registry-1.docker.io/bitnamicharts | postgresql | 18.8.13 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| additionalObjects | list | `[]` | additional resources to deploy. Those objects are templated. |
| authentik | object | See [values.yaml] | Authentik configuration. See the [authentik configuration docs] for details about which values are accepted here. See the note at the top of that page for details about transforming environment variable names into values here. |
| authentik.email.from | string | `""` | Email from address, can either be in the format "foo@bar.baz" or "authentik <foo@bar.baz>" |
| authentik.email.host | string | `""` | SMTP Server emails are sent from, fully optional |
| authentik.email.password | string | `""` | SMTP credentials, when left empty, no authentication will be done |
| authentik.email.port | int | `587` | SMTP server port |
| authentik.email.timeout | int | `30` | Connection timeout |
| authentik.email.use_ssl | bool | `false` | Use SSL. Enable either use_tls or use_ssl, they can't be enabled at the same time. |
| authentik.email.use_tls | bool | `false` | Use StartTLS. Enable either use_tls or use_ssl, they can't be enabled at the same time. |
| authentik.email.username | string | `""` | SMTP credentials, when left empty, no authentication will be done |
| authentik.enabled | bool | `true` | whether to create the authentik configuration secret |
| authentik.error_reporting.enabled | bool | `false` | This sends anonymous usage-data, stack traces on errors and performance data to sentry.beryju.org, and is fully opt-in |
| authentik.error_reporting.environment | string | `"k8s"` | This is a string that is sent to sentry with your error reports |
| authentik.error_reporting.send_pii | bool | `false` | Send PII (Personally identifiable information) data to sentry |
| authentik.events.context_processors.asn | string | `"/geoip/GeoLite2-ASN.mmdb"` | Path for the GeoIP ASN database. If the file doesn't exist, GeoIP features are disabled. |
| authentik.events.context_processors.geoip | string | `"/geoip/GeoLite2-City.mmdb"` | Path for the GeoIP City database. If the file doesn't exist, GeoIP features are disabled. |
| authentik.existingSecret.secretName | string | `""` | name of an existing secret to use for authentik configuration. This secret must contain keys matching configuration option names, see the docs for the full list of configuration options https://docs.goauthentik.io/install-config/configuration/ |
| authentik.log_level | string | `"info"` | Log level for server and worker |
| authentik.outposts.container_image_base | string | `"ghcr.io/goauthentik/%(type)s:%(version)s"` | Template used for managed outposts. The following placeholders can be used %(type)s - the type of the outpost %(version)s - version of your authentik install %(build_hash)s - only for beta versions, the build hash of the image |
| authentik.postgresql.host | string | `{{ .Release.Name }}-postgresql` | set the postgresql hostname to talk to if unset and .Values.postgresql.enabled == true, will generate the default |
| authentik.postgresql.name | string | `authentik` | postgresql Database name |
| authentik.postgresql.password | string | `""` | postgresql password |
| authentik.postgresql.port | int | `5432` | postgresql port |
| authentik.postgresql.user | string | `authentik` | postgresql Username |
| authentik.secret_key | string | `""` | Secret key used for cookie singing and unique user IDs, don't change this after the first install |
| authentik.web.path | string | `"/"` | Relative path the authentik instance will be available at. Value _must_ contain both a leading and trailing slash. |
| blueprints.configMaps | list | `[]` | List of config maps to mount blueprints from. Only keys in the configMap ending with `.yaml` will be discovered and applied. |
| blueprints.secrets | list | `[]` | List of secrets to mount blueprints from. Only keys in the secret ending with `.yaml` will be discovered and applied. |
| fullnameOverride | string | `""` | String to fully override `"authentik.fullname"`. Prefer using global.fullnameOverride if possible |
| geoip.accountId | string | `""` | sign up under https://www.maxmind.com/en/geolite2/signup |
| geoip.containerSecurityContext | object | See [values.yaml] | GeoIP container-level security context |
| geoip.editionIds | string | `"GeoLite2-City GeoLite2-ASN"` |  |
| geoip.enabled | bool | `false` | enable GeoIP sidecars for the authentik server and worker pods |
| geoip.env | list | `[]` (See [values.yaml]) | Environment variables to pass to the GeoIP containers |
| geoip.envFrom | list | `[]` (See [values.yaml]) | envFrom to pass to the GeoIP containers |
| geoip.existingSecret.accountId | string | `"account_id"` | key in the secret containing the account ID |
| geoip.existingSecret.licenseKey | string | `"license_key"` | key in the secret containing the license key |
| geoip.existingSecret.secretName | string | `""` | name of an existing secret to use instead of values above |
| geoip.image.digest | string | `""` | If defined, an image digest for GeoIP images |
| geoip.image.pullPolicy | string | `"IfNotPresent"` | If defined, an imagePullPolicy for GeoIP images |
| geoip.image.repository | string | `"ghcr.io/maxmind/geoipupdate"` | If defined, a repository for GeoIP images |
| geoip.image.tag | string | `"v7.1.1"` | If defined, a tag for GeoIP images |
| geoip.licenseKey | string | `""` | sign up under https://www.maxmind.com/en/geolite2/signup |
| geoip.resources | object | `{}` | Resource limits and requests for GeoIP containers |
| geoip.updateInterval | int | `8` | GeoIP update frequency, in hours |
| geoip.volumeMounts | list | `[]` | Additional volumeMounts to the GeoIP containers. Make sure the volumes exists for the server and the worker. |
| global.addPrometheusAnnotations | bool | `false` | Add Prometheus scrape annotations to all metrics services. This can be used as an alternative to the ServiceMonitors. |
| global.additionalLabels | object | `{}` | Common labels for all resources. |
| global.affinity.nodeAffinity.matchExpressions | list | `[]` | Default match expressions for node affinity |
| global.affinity.nodeAffinity.type | string | `"hard"` | Default node affinity rules. Either `none`, `soft` or `hard` |
| global.affinity.podAntiAffinity | string | `"soft"` | Default pod anti-affinity rules. Either: `none`, `soft` or `hard` |
| global.deploymentAnnotations | object | `{}` | Annotations for all deployed Deployments |
| global.deploymentStrategy | object | `{}` | Deployment strategy for all deployed Deployments |
| global.env | list | `[]` (See [values.yaml]) | Environment variables to pass to all deployed Deployments. Does not apply to GeoIP See configuration options at https://goauthentik.io/docs/installation/configuration/ |
| global.envFrom | list | `[]` (See [values.yaml]) | envFrom to pass to all deployed Deployments. Does not apply to GeoIP |
| global.fullnameOverride | string | `""` | String to fully override `"authentik.fullname"` |
| global.hostAliases | list | `[]` | Mapping between IP and hostnames that will be injected as entries in the pod's hosts files |
| global.image.digest | string | `""` | If defined, an image digest applied to all authentik deployments |
| global.image.pullPolicy | string | `"IfNotPresent"` | If defined, an imagePullPolicy applied to all authentik deployments |
| global.image.repository | string | `"ghcr.io/goauthentik/server"` | If defined, a repository applied to all authentik deployments |
| global.image.tag | string | `""` | Overrides the global authentik whose default is the chart appVersion |
| global.imagePullSecrets | list | `[]` | Secrets with credentials to pull images from a private registry |
| global.nameOverride | string | `""` | Provide a name in place of `authentik` |
| global.namespaceOverride | string | `""` | A custom namespace to override the default namespace for the deployed resources. |
| global.nodeSelector | object | `{}` | Default node selector for all components |
| global.podAnnotations | object | `{}` | Annotations for all deployed pods |
| global.podLabels | object | `{}` | Labels for all deployed pods |
| global.priorityClassName | string | `""` | Default priority class for all components |
| global.revisionHistoryLimit | int | `3` |  |
| global.secretAnnotations | object | `{}` | Annotations for all deployed secrets |
| global.security.allowInsecureImages | bool | `true` |  |
| global.securityContext | object | `{}` (See [values.yaml]) | Toggle and define pod-level security context. |
| global.tolerations | list | `[]` | Default tolerations for all components |
| global.topologySpreadConstraints | list | `[]` | Default [TopologySpreadConstraints] rules for all components # Ref: https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/ |
| global.volumeMounts | list | `[]` (See [values.yaml]) | Additional volumeMounts to all deployed Deployments. Does not apply to GeoIP |
| global.volumes | list | `[]` (See [values.yaml]) | Additional volumes to all deployed Deployments. |
| kubeVersionOverride | string | `""` | Override the Kubernetes version, which is used to evaluate certain manifests |
| nameOverride | string | `""` | Provide a name in place of `authentik`. Prefer using global.nameOverride if possible |
| postgresql.auth.database | string | `"authentik"` |  |
| postgresql.auth.username | string | `"authentik"` |  |
| postgresql.backup.resourcesPreset | string | `"none"` |  |
| postgresql.enabled | bool | `false` | enable the Bitnami PostgreSQL chart. Refer to https://github.com/bitnami/charts/blob/main/bitnami/postgresql/ for possible values. |
| postgresql.image.registry | string | `"docker.io"` |  |
| postgresql.image.repository | string | `"library/postgres"` |  |
| postgresql.image.tag | string | `"17.11-bookworm"` |  |
| postgresql.metrics.image.repository | string | `"prometheuscommunity/postgres-exporter"` |  |
| postgresql.metrics.image.tag | string | `"v0.19.1"` |  |
| postgresql.metrics.resourcesPreset | string | `"none"` |  |
| postgresql.passwordUpdateJob.resourcesPreset | string | `"none"` |  |
| postgresql.primary.args[0] | string | `"-c"` |  |
| postgresql.primary.args[1] | string | `"config_file=/bitnami/postgresql/conf/postgresql.conf"` |  |
| postgresql.primary.args[2] | string | `"-c"` |  |
| postgresql.primary.args[3] | string | `"hba_file=/bitnami/postgresql/conf/pg_hba.conf"` |  |
| postgresql.primary.configuration | string | `"listen_addresses = '*'\nport = '5432'\nwal_level = 'replica'\nfsync = 'on'\nhot_standby = 'on'\nlog_connections = 'false'\nlog_disconnections = 'false'\nlog_hostname = 'false'\nclient_min_messages = 'error'\ninclude_dir = 'conf.d'\n"` |  |
| postgresql.primary.containerSecurityContext.readOnlyRootFilesystem | bool | `true` |  |
| postgresql.primary.extendedConfiguration | string | `"max_connections = 500\n"` |  |
| postgresql.primary.extraEnvVars[0].name | string | `"POSTGRES_DB"` |  |
| postgresql.primary.extraEnvVars[0].value | string | `"{{ (include \"postgresql.v1.database\" .) }}"` |  |
| postgresql.primary.extraVolumeMounts[0].mountPath | string | `"/var/run/postgresql"` |  |
| postgresql.primary.extraVolumeMounts[0].name | string | `"postgresql-socket"` |  |
| postgresql.primary.extraVolumes[0].emptyDir | object | `{}` |  |
| postgresql.primary.extraVolumes[0].name | string | `"postgresql-socket"` |  |
| postgresql.primary.pgHbaConfiguration | string | `"host     all             all             0.0.0.0/0               scram-sha-256\nhost     all             all             ::/0                    scram-sha-256\nlocal    all             all                                     scram-sha-256\nhost     all             all        127.0.0.1/32                 scram-sha-256\nhost     all             all        ::1/128                      scram-sha-256\n"` |  |
| postgresql.primary.resourcesPreset | string | `"none"` |  |
| postgresql.readReplicas.resourcesPreset | string | `"none"` |  |
| postgresql.volumePermissions.image.repository | string | `"debian"` |  |
| postgresql.volumePermissions.image.tag | string | `"13-slim"` |  |
| postgresql.volumePermissions.resourcesPreset | string | `"none"` |  |
| prometheus.rules.additionalRuleGroupAnnotations | object | `{}` | PrometheusRuleGroup additional annotations |
| prometheus.rules.annotations | object | `{}` | PrometheusRule annotations |
| prometheus.rules.enabled | bool | `false` |  |
| prometheus.rules.labels | object | `{}` | PrometheusRule labels |
| prometheus.rules.namespace | string | `""` | PrometheusRule namespace |
| prometheus.rules.selector | object | `{}` | PrometheusRule selector |
| server.affinity | object | `{}` (defaults to the global.affinity preset) | Assign custom [affinity] rules to the deployment |
| server.automountServiceAccountToken | bool | `nil` | automount behavior for service account token in server pods. Only applies if server.serviceAccountName is set. |
| server.autoscaling.behavior | object | `{}` | Configures the scaling behavior of the target in both Up and Down directions. |
| server.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler ([HPA]) for the authentik server |
| server.autoscaling.maxReplicas | int | `5` | Maximum number of replicas for the authentik server [HPA] |
| server.autoscaling.metrics | list | `[]` | Configures custom HPA metrics for the authentik server Ref: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ |
| server.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the authentik server [HPA] |
| server.autoscaling.targetCPUUtilizationPercentage | int | `50` | Average CPU utilization percentage for the authentik server [HPA] |
| server.autoscaling.targetMemoryUtilizationPercentage | string | `nil` | Average memory utilization percentage for the authentik server [HPA] |
| server.containerPorts.http | int | `9000` | http container port |
| server.containerPorts.https | int | `9443` | https container port |
| server.containerPorts.metrics | int | `9300` | metrics container port |
| server.containerSecurityContext | object | See [values.yaml] | authentik server container-level security context |
| server.deploymentAnnotations | object | `{}` | Annotations to be added to the authentik server Deployment |
| server.deploymentStrategy | object | `{}` (defaults to global.deploymentStrategy) | Deployment strategy to be added to the authentik server Deployment |
| server.dnsConfig | object | `{}` | [DNS configuration] |
| server.dnsPolicy | string | `""` | Alternative DNS policy for authentik server pods |
| server.enabled | bool | `true` | whether to enable server resources |
| server.env | list | `[]` (See [values.yaml]) | Environment variables to pass to the authentik server. Does not apply to GeoIP See configuration options at https://goauthentik.io/docs/installation/configuration/ |
| server.envFrom | list | `[]` (See [values.yaml]) | envFrom to pass to the authentik server. Does not apply to GeoIP |
| server.extraContainers | list | `[]` | Additional containers to be added to the authentik server pod # Note: Supports use of custom Helm templates |
| server.hostNetwork | bool | `false` | Host Network for authentik server pods |
| server.image.digest | string | `""` (defaults to global.image.digest) | Digest to use to the authentik server |
| server.image.pullPolicy | string | `""` (defaults to global.image.pullPolicy) | Image pull policy to use to the authentik server |
| server.image.repository | string | `""` (defaults to global.image.repository) | Repository to use to the authentik server |
| server.image.tag | string | `""` (defaults to global.image.tag) | Tag to use to the authentik server |
| server.imagePullSecrets | list | `[]` (defaults to global.imagePullSecrets) | Secrets with credentials to pull images from a private registry |
| server.ingress.annotations | object | `{}` | additional ingress annotations |
| server.ingress.enabled | bool | `false` | enable an ingress resource for the authentik server |
| server.ingress.extraPaths | list | `[]` | additional ingress paths |
| server.ingress.hosts | list | `[]` | List of ingress hosts |
| server.ingress.https | bool | `false` | uses `server.service.servicePortHttps` instead of `server.service.servicePortHttp` |
| server.ingress.ingressClassName | string | `""` | defines which ingress controller will implement the resource |
| server.ingress.labels | object | `{}` | additional ingress labels |
| server.ingress.pathType | string | `"Prefix"` | Ingress path type. One of `Exact`, `Prefix` or `ImplementationSpecific` |
| server.ingress.paths | list | `["{{ .Values.authentik.web.path }}"]` | List of ingress paths |
| server.ingress.tls | list | `[]` | ingress TLS configuration |
| server.initContainers | list | `[]` | Init containers to add to the authentik server pod # Note: Supports use of custom Helm templates |
| server.lifecycle | object | `{}` | Specify postStart and preStop lifecycle hooks for you authentik server container |
| server.livenessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| server.livenessProbe.httpGet.path | string | `"{{ .Values.authentik.web.path }}-/health/live/"` |  |
| server.livenessProbe.httpGet.port | string | `"http"` |  |
| server.livenessProbe.initialDelaySeconds | int | `5` | Number of seconds after the container has started before [probe] is initiated |
| server.livenessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| server.livenessProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| server.livenessProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| server.metrics.enabled | bool | `false` | deploy metrics service |
| server.metrics.service.annotations | object | `{}` | metrics service annotations |
| server.metrics.service.clusterIP | string | `""` | metrics service clusterIP. `None` makes a "headless service" (no virtual IP) |
| server.metrics.service.labels | object | `{}` | metrics service labels |
| server.metrics.service.portName | string | `"metrics"` | metrics service port name |
| server.metrics.service.servicePort | int | `9300` | metrics service port |
| server.metrics.service.type | string | `"ClusterIP"` | metrics service type |
| server.metrics.serviceMonitor.annotations | object | `{}` | Prometheus ServiceMonitor annotations |
| server.metrics.serviceMonitor.enabled | bool | `false` | enable a prometheus ServiceMonitor |
| server.metrics.serviceMonitor.interval | string | `"30s"` | Prometheus ServiceMonitor interval |
| server.metrics.serviceMonitor.labels | object | `{}` | Prometheus ServiceMonitor labels |
| server.metrics.serviceMonitor.metricRelabelings | list | `[]` | Prometheus [MetricsRelabelConfigs] to apply to samples before ingestion |
| server.metrics.serviceMonitor.namespace | string | `""` | Prometheus ServiceMonitor namespace |
| server.metrics.serviceMonitor.relabelings | list | `[]` | Prometheus [RelabelConfigs] to apply to samples before scraping |
| server.metrics.serviceMonitor.scheme | string | `""` | Prometheus ServiceMonitor scheme |
| server.metrics.serviceMonitor.scrapeTimeout | string | `"3s"` | Prometheus ServiceMonitor scrape timeout |
| server.metrics.serviceMonitor.selector | object | `{}` | Prometheus ServiceMonitor selector |
| server.metrics.serviceMonitor.tlsConfig | object | `{}` | Prometheus ServiceMonitor tlsConfig |
| server.name | string | `"server"` | authentik server name |
| server.nodeSelector | object | `{}` (defaults to global.nodeSelector) | [Node selector] |
| server.pdb.annotations | object | `{}` | Annotations to be added to the authentik server pdb |
| server.pdb.enabled | bool | `false` | Deploy a [PodDistrubtionBudget] for the authentik server |
| server.pdb.labels | object | `{}` | Labels to be added to the authentik server pdb |
| server.pdb.maxUnavailable | string | `""` | Number of pods that are unavailable after eviction as number or percentage (eg.: 50%) # Has higher precedence over `server.pdb.minAvailable` |
| server.pdb.minAvailable | string | `""` (defaults to 0 if not specified) | Number of pods that are available after eviction as number or percentage (eg.: 50%) |
| server.podAnnotations | object | `{}` | Annotations to be added to the authentik server pods |
| server.podLabels | object | `{}` | Labels to be added to the authentik server pods |
| server.priorityClassName | string | `""` (defaults to global.priorityClassName) | Prority class for the authentik server pods |
| server.readinessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| server.readinessProbe.httpGet.path | string | `"{{ .Values.authentik.web.path }}-/health/ready/"` |  |
| server.readinessProbe.httpGet.port | string | `"http"` |  |
| server.readinessProbe.initialDelaySeconds | int | `5` | Number of seconds after the container has started before [probe] is initiated |
| server.readinessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| server.readinessProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| server.readinessProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| server.replicas | int | `1` | The number of server pods to run |
| server.resources | object | `{}` | Resource limits and requests for the authentik server |
| server.route.main.additionalRules | list | `[]` | Additional custom rules that can be added to the route |
| server.route.main.annotations | object | `{}` | Route annotations |
| server.route.main.apiVersion | string | `"gateway.networking.k8s.io/v1"` | Set the route apiVersion |
| server.route.main.enabled | bool | `false` | enable an HTTPRoute resource for the authentik server. Be aware that this is an early beta of this feature. We don't guarantee this works and is subject to change. |
| server.route.main.filters | list | `[]` | Route filters |
| server.route.main.hostnames | list | `[]` | Route hostnames |
| server.route.main.https | bool | `false` | uses `server.service.servicePortHttps` instead of `server.service.servicePortHttp` |
| server.route.main.httpsRedirect | bool | `false` | Create http route for redirect (https://gateway-api.sigs.k8s.io/guides/http-redirect-rewrite/#http-to-https-redirects). Take care that you only enable this on the http listener of the gateway to avoid an infinite redirect. Matches, filters and additionalRules will be ignored if this is set to true |
| server.route.main.kind | string | `"HTTPRoute"` | Set the route kind |
| server.route.main.labels | object | `{}` | Route labels |
| server.route.main.matches | list | `[{"path":{"type":"PathPrefix","value":"{{ .Values.authentik.web.path }}"}}]` | Route matches |
| server.route.main.parentRefs | list | `[]` | Reference to parent gateways |
| server.securityContext | object | `{}` (See [values.yaml]) | authentik server pod-level security context |
| server.service.annotations | object | `{}` | authentik server service annotations |
| server.service.externalIPs | list | `[]` | authentik server service external IPs |
| server.service.externalTrafficPolicy | string | `""` | Denotes if this service desires to route external traffic to node-local or cluster-wide endpoints |
| server.service.labels | object | `{}` | authentik server service labels |
| server.service.loadBalancerIP | string | `""` | LoadBalancer will get created with the IP specified in this field |
| server.service.loadBalancerSourceRanges | list | `[]` | Source IP ranges to allow access to service from |
| server.service.nodePortHttp | int | `30080` | authentik server service http port for NodePort service type (only if `server.service.type` is set to `NodePort`) |
| server.service.nodePortHttps | int | `30443` | authentik server service https port for NodePort service type (only if `server.service.type` is set to `NodePort`) |
| server.service.servicePortHttp | int | `80` | authentik server service http port |
| server.service.servicePortHttpName | string | `"http"` | authentik server service http port name |
| server.service.servicePortHttps | int | `443` | authentik server service https port |
| server.service.servicePortHttpsName | string | `"https"` | authentik server service https port name |
| server.service.sessionAffinity | string | `""` | Used to maintain session affinity. Supports `ClientIP` and `None` |
| server.service.sessionAffinityConfig | object | `{}` | Session affinity configuration |
| server.service.type | string | `"ClusterIP"` | authentik server service type |
| server.serviceAccountName | string | `nil` | serviceAccount to use for authentik server pods |
| server.startupProbe.failureThreshold | int | `60` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| server.startupProbe.httpGet.path | string | `"{{ .Values.authentik.web.path }}-/health/live/"` |  |
| server.startupProbe.httpGet.port | string | `"http"` |  |
| server.startupProbe.initialDelaySeconds | int | `5` | Number of seconds after the container has started before [probe] is initiated |
| server.startupProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| server.startupProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| server.startupProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| server.terminationGracePeriodSeconds | int | `30` | terminationGracePeriodSeconds for container lifecycle hook |
| server.tolerations | list | `[]` (defaults to global.tolerations) | [Tolerations] for use with node taints |
| server.topologySpreadConstraints | list | `[]` (defaults to global.topologySpreadConstraints) | Assign custom [TopologySpreadConstraints] rules to the authentik server # Ref: https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/ # If labelSelector is left out, it will default to the labelSelector configuration of the deployment |
| server.volumeMounts | list | `[]` | Additional volumeMounts to the authentik server main container |
| server.volumes | list | `[]` | Additional volumes to the authentik server pod |
| serviceAccount.annotations | object | `{}` | additional service account annotations |
| serviceAccount.create | bool | `true` | Create service account. Needed for managed outposts |
| serviceAccount.fullnameOverride | string | `"authentik"` |  |
| serviceAccount.serviceAccountSecret.enabled | bool | `false` |  |
| worker.affinity | object | `{}` (defaults to the global.affinity preset) | Assign custom [affinity] rules to the deployment |
| worker.automountServiceAccountToken | bool | `nil` | automount behavior for service account token in worker pods. Only applies if worker.serviceAccountName is set. |
| worker.autoscaling.behavior | object | `{}` | Configures the scaling behavior of the target in both Up and Down directions. |
| worker.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler ([HPA]) for the authentik worker |
| worker.autoscaling.maxReplicas | int | `5` | Maximum number of replicas for the authentik worker [HPA] |
| worker.autoscaling.metrics | list | `[]` | Configures custom HPA metrics for the authentik worker Ref: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ |
| worker.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the authentik worker [HPA] |
| worker.autoscaling.targetCPUUtilizationPercentage | int | `50` | Average CPU utilization percentage for the authentik worker [HPA] |
| worker.autoscaling.targetMemoryUtilizationPercentage | string | `nil` | Average memory utilization percentage for the authentik worker [HPA] |
| worker.containerPorts.http | int | `9000` | http container port |
| worker.containerPorts.metrics | int | `9300` | metrics container port |
| worker.containerSecurityContext | object | See [values.yaml] | authentik worker container-level security context |
| worker.deploymentAnnotations | object | `{}` | Annotations to be added to the authentik worker Deployment |
| worker.deploymentStrategy | object | `{}` (defaults to global.deploymentStrategy) | Deployment strategy to be added to the authentik worker Deployment |
| worker.dnsConfig | object | `{}` | [DNS configuration] |
| worker.dnsPolicy | string | `""` | Alternative DNS policy for authentik worker pods |
| worker.enabled | bool | `true` | whether to enable worker resources |
| worker.env | list | `[]` (See [values.yaml]) | Environment variables to pass to the authentik worker. Does not apply to GeoIP See configuration options at https://goauthentik.io/docs/installation/configuration/ |
| worker.envFrom | list | `[]` (See [values.yaml]) | envFrom to pass to the authentik worker. Does not apply to GeoIP |
| worker.extraContainers | list | `[]` | Additional containers to be added to the authentik worker pod # Note: Supports use of custom Helm templates |
| worker.hostNetwork | bool | `false` | Host Network for authentik worker pods |
| worker.image.digest | string | `""` (defaults to global.image.digest) | Digest to use to the authentik worker |
| worker.image.pullPolicy | string | `""` (defaults to global.image.pullPolicy) | Image pull policy to use to the authentik worker |
| worker.image.repository | string | `""` (defaults to global.image.repository) | Repository to use to the authentik worker |
| worker.image.tag | string | `""` (defaults to global.image.tag) | Tag to use to the authentik worker |
| worker.imagePullSecrets | list | `[]` (defaults to global.imagePullSecrets) | Secrets with credentials to pull images from a private registry |
| worker.initContainers | list | `[]` | Init containers to add to the authentik worker pod # Note: Supports use of custom Helm templates |
| worker.lifecycle | object | `{}` | Specify postStart and preStop lifecycle hooks for you authentik worker container |
| worker.livenessProbe.exec.command[0] | string | `"ak"` |  |
| worker.livenessProbe.exec.command[1] | string | `"healthcheck"` |  |
| worker.livenessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| worker.livenessProbe.initialDelaySeconds | int | `5` | Number of seconds after the container has started before [probe] is initiated |
| worker.livenessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| worker.livenessProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| worker.livenessProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| worker.metrics.enabled | bool | `false` | deploy metrics service |
| worker.metrics.service.annotations | object | `{}` | metrics service annotations |
| worker.metrics.service.clusterIP | string | `""` | metrics service clusterIP. `None` makes a "headless service" (no virtual IP) |
| worker.metrics.service.labels | object | `{}` | metrics service labels |
| worker.metrics.service.portName | string | `"metrics"` | metrics service port name |
| worker.metrics.service.servicePort | int | `9300` | metrics service port |
| worker.metrics.service.type | string | `"ClusterIP"` | metrics service type |
| worker.metrics.serviceMonitor.annotations | object | `{}` | Prometheus ServiceMonitor annotations |
| worker.metrics.serviceMonitor.enabled | bool | `false` | enable a prometheus ServiceMonitor |
| worker.metrics.serviceMonitor.interval | string | `"30s"` | Prometheus ServiceMonitor interval |
| worker.metrics.serviceMonitor.labels | object | `{}` | Prometheus ServiceMonitor labels |
| worker.metrics.serviceMonitor.metricRelabelings | list | `[]` | Prometheus [MetricsRelabelConfigs] to apply to samples before ingestion |
| worker.metrics.serviceMonitor.namespace | string | `""` | Prometheus ServiceMonitor namespace |
| worker.metrics.serviceMonitor.relabelings | list | `[]` | Prometheus [RelabelConfigs] to apply to samples before scraping |
| worker.metrics.serviceMonitor.scheme | string | `""` | Prometheus ServiceMonitor scheme |
| worker.metrics.serviceMonitor.scrapeTimeout | string | `"3s"` | Prometheus ServiceMonitor scrape timeout |
| worker.metrics.serviceMonitor.selector | object | `{}` | Prometheus ServiceMonitor selector |
| worker.metrics.serviceMonitor.tlsConfig | object | `{}` | Prometheus ServiceMonitor tlsConfig |
| worker.name | string | `"worker"` | authentik worker name |
| worker.nodeSelector | object | `{}` (defaults to global.nodeSelector) | [Node selector] |
| worker.pdb.annotations | object | `{}` | Annotations to be added to the authentik worker pdb |
| worker.pdb.enabled | bool | `false` | Deploy a [PodDistrubtionBudget] for the authentik worker |
| worker.pdb.labels | object | `{}` | Labels to be added to the authentik worker pdb |
| worker.pdb.maxUnavailable | string | `""` | Number of pods that are unavailable after eviction as number or percentage (eg.: 50%) # Has higher precedence over `worker.pdb.minAvailable` |
| worker.pdb.minAvailable | string | `""` (defaults to 0 if not specified) | Number of pods that are available after eviction as number or percentage (eg.: 50%) |
| worker.podAnnotations | object | `{}` | Annotations to be added to the authentik worker pods |
| worker.podLabels | object | `{}` | Labels to be added to the authentik worker pods |
| worker.priorityClassName | string | `""` (defaults to global.priorityClassName) | Prority class for the authentik worker pods |
| worker.readinessProbe.exec.command[0] | string | `"ak"` |  |
| worker.readinessProbe.exec.command[1] | string | `"healthcheck"` |  |
| worker.readinessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| worker.readinessProbe.initialDelaySeconds | int | `5` | Number of seconds after the container has started before [probe] is initiated |
| worker.readinessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| worker.readinessProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| worker.readinessProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| worker.replicas | int | `1` | The number of worker pods to run |
| worker.resources | object | `{}` | Resource limits and requests for the authentik worker |
| worker.securityContext | object | `{}` (See [values.yaml]) | authentik worker pod-level security context |
| worker.serviceAccountName | string | `nil` | serviceAccount to use for authentik worker pods. If set, overrides the value used when serviceAccount.create is true |
| worker.startupProbe.exec.command[0] | string | `"ak"` |  |
| worker.startupProbe.exec.command[1] | string | `"healthcheck"` |  |
| worker.startupProbe.failureThreshold | int | `60` | Minimum consecutive failures for the [probe] to be considered failed after having succeeded |
| worker.startupProbe.initialDelaySeconds | int | `30` | Number of seconds after the container has started before [probe] is initiated |
| worker.startupProbe.periodSeconds | int | `10` | How often (in seconds) to perform the [probe] |
| worker.startupProbe.successThreshold | int | `1` | Minimum consecutive successes for the [probe] to be considered successful after having failed |
| worker.startupProbe.timeoutSeconds | int | `3` | Number of seconds after which the [probe] times out |
| worker.terminationGracePeriodSeconds | int | `30` | terminationGracePeriodSeconds for container lifecycle hook |
| worker.tolerations | list | `[]` (defaults to global.tolerations) | [Tolerations] for use with node taints |
| worker.topologySpreadConstraints | list | `[]` (defaults to global.topologySpreadConstraints) | Assign custom [TopologySpreadConstraints] rules to the authentik worker # Ref: https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/ # If labelSelector is left out, it will default to the labelSelector configuration of the deployment |
| worker.volumeMounts | list | `[]` | Additional volumeMounts to the authentik worker main container |
| worker.volumes | list | `[]` | Additional volumes to the authentik worker pod |

---
[affinity]: https://kubernetes.io/docs/concepts/configuration/assign-pod-node/
[DNS configuration]: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
[HPA]: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
[MetricRelabelConfigs]: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#metric_relabel_configs
[Node selector]: https://kubernetes.io/docs/user-guide/node-selection/
[PodDisruptionBudget]: https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets
[probe]: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes
[RelabelConfigs]: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#relabel_config
[Tolerations]: https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/
[TopologySpreadConstraints]: https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/
[values.yaml]: values.yaml
[authentik configuration docs]: https://docs.goauthentik.io/install-config/configuration/
