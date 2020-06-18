# Kubernetes

For a mid to high-load installation, Kubernetes is recommended. passbook is installed using a helm-chart.

```
# Default values for passbook.
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.
# passbook version to use. Defaults to latest stable version
# image:
#   tag:

nameOverride: ""

config:
  # Optionally specify fixed secret_key, otherwise generated automatically
  # secret_key: _k*@6h2u2@q-dku57hhgzb7tnx*ba9wodcb^s9g0j59@=y(@_o
  # Enable error reporting
  error_reporting: false
  # Log level used by web and worker
  # Can be either debug, info, warning, error
  log_level: warning

# This Helm chart ships with built-in Prometheus ServiceMonitors and Rules.
# This requires the CoreOS Prometheus Operator.
monitoring:
  enabled: false

# Enable Database Backups to S3
# backup:
#   access_key: access-key
#   secret_key: secret-key
#   bucket: s3-bucket
#   host: s3-host

ingress:
  enabled: false
  annotations: {}
    # kubernetes.io/ingress.class: nginx
    # kubernetes.io/tls-acme: "true"
  path: /
  hosts:
    - passbook.k8s.local
  tls: []
  #  - secretName: chart-example-tls
  #    hosts:
  #      - passbook.k8s.local

# These settings configure the packaged PostgreSQL and Redis chart.
postgresql:
  postgresqlDatabase: passbook

redis:
  cluster:
    enabled: false
  master:
    persistence:
      enabled: false
    # https://stackoverflow.com/a/59189742
    disableCommands: []
```
