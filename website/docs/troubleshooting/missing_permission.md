---
title: Missing Permissions system_exception events
---

This error can occur during initial setup, when authentik bootstraps the embedded Outpost, while the database migrations are not finished yet.

The error should be temporary and not occur after initial installation.

If it does, you can run the following command to ensure all permissions exist:

```
docker-compose run --rm worker repair_permissions
```

or, for Kubernetes, run

```
kubectl exec -it deployment/authentik-worker -c authentik -- ak repair_permissions
```

If the error persists after running this command, please open an Issue on [GitHub](https://github.com/goauthentik/authentik/issues/)
