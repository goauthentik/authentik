---
title: Missing admin group
---

If all of the Admin groups have been deleted, or misconfigured during sync, you can use the following command to gain access back.

Run the following command, where _username_ is the user you want to add to the newly created group:

```
docker compose run --rm server create_admin_group username
```

or, for Kubernetes, run

```
kubectl exec -it deployment/authentik-worker -c authentik -- ak create_admin_group username
```
