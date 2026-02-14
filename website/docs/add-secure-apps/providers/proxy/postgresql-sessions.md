---
title: PostgreSQL Session Persistence
---

Embedded proxy outposts (running within authentik Core) use PostgreSQL for session storage by default. However, **non-embedded outposts** (standalone deployments) use filesystem-based sessions by default, which means sessions are lost when the outpost container restarts.

This guide explains how to configure **non-embedded proxy outposts** to use PostgreSQL for session persistence, enabling sessions to survive container restarts and allowing multiple outpost replicas to share session storage.

## Why PostgreSQL Sessions?

For non-embedded outposts deployed in production environments (especially Kubernetes), filesystem-based sessions have limitations:

- Sessions are lost on container restart or pod rescheduling
- Each outpost replica maintains its own session store (no sharing)
- Deployments and updates cause user logouts

By configuring PostgreSQL sessions, non-embedded outposts gain the same benefits as embedded outposts:
- Sessions persist across restarts
- Multiple replicas can share the same session database
- Users maintain their sessions during deployments

## Configuration

To enable PostgreSQL session persistence for non-embedded outposts, configure the following settings when creating or editing an outpost:

### Session Backend

Set the `session_backend` field to `postgres` or `postgresql`. This tells the non-embedded outpost to use PostgreSQL instead of filesystem-based sessions.

:::note
Embedded outposts (the outpost running within authentik Core) already use PostgreSQL sessions by default and do not require this configuration.
:::

### For Kubernetes Deployments

When deploying on Kubernetes, authentik can automatically inject PostgreSQL credentials and mount necessary secrets:

#### Basic Configuration

1. **PostgreSQL Secret**: Create or use an existing Kubernetes secret containing PostgreSQL connection variables:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: authentik-postgresql
     namespace: authentik
   stringData:
     AUTHENTIK_POSTGRESQL__HOST: "postgres.database.svc.cluster.local"
     AUTHENTIK_POSTGRESQL__PORT: "5432"
     AUTHENTIK_POSTGRESQL__NAME: "authentik"
     AUTHENTIK_POSTGRESQL__USER: "authentik"
     AUTHENTIK_POSTGRESQL__PASSWORD: "your-password"
   ```

2. **Outpost Configuration**: In the outpost's advanced settings, set:
   - `session_backend`: `postgres`
   - `kubernetes_postgresql_secret_name`: `authentik-postgresql`

authentik will automatically inject this secret via `envFrom` in the outpost deployment.

#### Using File-based Credentials (Recommended for Security)

For enhanced security, you can store credentials in files and reference them using `file://` URIs:

1. **Credentials Secret**: Create a secret with actual credential files:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: postgres-credentials
     namespace: authentik
   stringData:
     username: "authentik"
     password: "your-secure-password"
     database: "authentik"
   ```

2. **PostgreSQL Configuration Secret**: Reference the files using `file://` URIs:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: authentik-postgresql
     namespace: authentik
   stringData:
     AUTHENTIK_POSTGRESQL__HOST: "postgres.database.svc.cluster.local"
     AUTHENTIK_POSTGRESQL__PORT: "5432"
     AUTHENTIK_POSTGRESQL__USER: "file:///postgres-creds/username"
     AUTHENTIK_POSTGRESQL__PASSWORD: "file:///postgres-creds/password"
     AUTHENTIK_POSTGRESQL__NAME: "file:///postgres-creds/database"
   ```

3. **Outpost Configuration**: Set the following in the outpost's advanced settings:
   - `session_backend`: `postgres`
   - `kubernetes_postgresql_secret_name`: `authentik-postgresql`
   - `kubernetes_postgresql_credentials_secret_name`: `postgres-credentials` (optional - auto-detected if not specified)

authentik will automatically:
- Detect the `file://` URIs in the PostgreSQL secret
- Extract the mount path from the URIs (e.g., `/postgres-creds`)
- Mount the credentials secret as a volume at the detected path
- The outpost will read the actual credentials from the mounted files

#### Auto-detection

If you don't specify `kubernetes_postgresql_credentials_secret_name`, authentik will automatically:
1. Scan all secrets in the namespace
2. Find secrets containing keys: `username`, `password`, and `database`
3. Mount the first matching secret

This automatic detection simplifies configuration but requires your credentials secret to follow the standard key naming convention.

### For Docker Deployments

When deploying with Docker Compose or standalone Docker, you need to manually configure PostgreSQL connection via environment variables:

```yaml
services:
  authentik_proxy:
    image: ghcr.io/goauthentik/proxy:latest
    environment:
      AUTHENTIK_HOST: https://authentik.company
      AUTHENTIK_TOKEN: <outpost-token>
      # PostgreSQL connection settings
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__PORT: 5432
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: your-password
    # ... other configuration
```

You can also use Docker secrets or external files for credentials:

```yaml
services:
  authentik_proxy:
    image: ghcr.io/goauthentik/proxy:latest
    environment:
      AUTHENTIK_HOST: https://authentik.company
      AUTHENTIK_TOKEN: <outpost-token>
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__PORT: 5432
      AUTHENTIK_POSTGRESQL__USER: file:///run/secrets/db_user
      AUTHENTIK_POSTGRESQL__PASSWORD: file:///run/secrets/db_password
      AUTHENTIK_POSTGRESQL__NAME: file:///run/secrets/db_name
    secrets:
      - db_user
      - db_password
      - db_name

secrets:
  db_user:
    file: ./secrets/db_user.txt
  db_password:
    file: ./secrets/db_password.txt
  db_name:
    file: ./secrets/db_name.txt
```

## Benefits

- **Parity with Embedded Outposts**: Non-embedded outposts can now achieve the same session persistence as embedded outposts
- **Persistence**: Sessions survive container restarts, providing a seamless user experience
- **Scalability**: Multiple outpost replicas can share the same session store
- **High Availability**: No session loss during pod rescheduling or deployments
- **Security**: Support for file-based credentials with automatic secret mounting in Kubernetes

## Database Requirements

- The PostgreSQL database should be the same one used by authentik Core
- The outpost will automatically create its session storage tables if they don't exist
- Sessions are stored in the `proxy_sessions` table with automatic cleanup of expired sessions

## Monitoring

Check the outpost logs for confirmation of PostgreSQL session backend:

```json
{
  "backend": "postgres",
  "event": "configured session backend",
  "level": "info",
  "logger": "authentik.outpost.proxyv2"
}
```

If there are connection issues, the outpost will log errors with details about the PostgreSQL connection failure.
