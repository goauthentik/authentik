# Upgrading to 0.12

This update brings these headline features:

- Rewrite Outpost state Logic, which now supports multiple concurrent Outpost instances.
- Add Kubernetes Integration for Outposts, which deploys and maintains Outposts with High Availability in a Kubernetes Cluster
- Add System Task Overview to see all background tasks, their status, the log output, and retry them
- Alerts now disappear automatically

## Upgrading

Docker-compose users can upgrade just as usual.

For Kubernetes users, there are some changes to the helm values.

The values change from

```yaml
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
```

to

```yaml
config:
  # Optionally specify fixed secret_key, otherwise generated automatically
  # secretKey: _k*@6h2u2@q-dku57hhgzb7tnx*ba9wodcb^s9g0j59@=y(@_o
  # Enable error reporting
  errorReporting:
    enabled: false
    environment: customer
    sendPii: false
  # Log level used by web and worker
  # Can be either debug, info, warning, error
  logLevel: warning
```

in order to be consistent with the rest of the settings.

There is also a new setting called `kubernetesIntegration`, which controls the Kubernetes integration for passbook. When enabled (the default), a Service Account is created, which allows passbook to deploy and update Outposts.
