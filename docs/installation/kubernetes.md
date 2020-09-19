# Kubernetes

For a mid to high-load installation, Kubernetes is recommended. passbook is installed using a helm-chart.

This installation automatically applies database migrations on startup. After the installation is done, you can use `pbadmin` as username and password.

```
###################################
# Values directly affecting passbook
###################################
image:
  name: beryju/passbook
  name_static: beryju/passbook-static
  tag: 0.10.4-stable

nameOverride: ""

serverReplicas: 1
workerReplicas: 1

config:
  # Optionally specify fixed secret_key, otherwise generated automatically
  # secret_key: _k*@6h2u2@q-dku57hhgzb7tnx*ba9wodcb^s9g0j59@=y(@_o
  # Enable error reporting
  error_reporting:
    enabled: false
    environment: customer
    send_pii: false
  # Log level used by web and worker
  # Can be either debug, info, warning, error
  log_level: warning

# Enable Database Backups to S3
# backup:
#   access_key: access-key
#   secret_key: secret-key
#   bucket: s3-bucket
#   host: s3-host

###################################
# Values controlling dependencies
###################################

install:
  postgresql: true
  redis: true

# These values influence the bundled postgresql and redis charts, but are also used by passbook to connect
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

ingress:
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
```
