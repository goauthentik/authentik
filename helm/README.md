# authentik Helm Chart

| Name                              | Default                 | Description |
|-----------------------------------|-------------------------|-------------|
| image.name                        | beryju/authentik         | Image used to run the authentik server and worker |
| image.name_static                 | beryju/authentik-static  | Image used to run the authentik static server (CSS and JS Files) |
| image.tag                         | 0.14.0-rc2              | Image tag |
| image.pullPolicy                  | IfNotPresent            | Image Pull Policy used for all deployments |
| serverReplicas                    | 1                       | Replicas for the Server deployment |
| workerReplicas                    | 1                       | Replicas for the Worker deployment |
| kubernetesIntegration             | true                    | Enable/disable the Kubernetes integration for authentik. This will create a service account for authentik to create and update outposts in authentik |
| config.secretKey                  |                         | Secret key used to sign session cookies, generate with `pwgen 50 1` for example. |
| config.errorReporting.enabled     | false                   | Enable/disable error reporting |
| config.errorReporting.environment | customer                | Environment sent with the error reporting |
| config.errorReporting.sendPii     | false                   | Whether to send Personally-identifiable data with the error reporting |
| config.logLevel                   | warning                 | Log level of authentik |
| backup.accessKey                  |                         | Optionally enable S3 Backup, Access Key |
| backup.secretKey                  |                         | Optionally enable S3 Backup, Secret Key |
| backup.bucket                     |                         | Optionally enable S3 Backup, Bucket |
| backup.region                     |                         | Optionally enable S3 Backup, Region |
| backup.host                       |                         | Optionally enable S3 Backup, to custom Endpoint like minio |
| ingress.annotations               | {}                      | Annotations for the ingress object |
| ingress.hosts                     | [authentik.k8s.local]    | Hosts which the ingress will match |
| ingress.tls                       | []                      | TLS Configuration, same as Ingress objects |
| install.postgresql                | true                    | Enables/disables the packaged PostgreSQL Chart
| install.redis                     | true                    | Enables/disables the packaged Redis Chart
| postgresql.postgresqlPassword     |                         | Password used for PostgreSQL, generated automatically.

For more info, see https://goauthentik.io/ and https://goauthentik.io/docs/installation/kubernetes/
