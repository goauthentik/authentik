---
title: Troubleshooting LDAP Synchronization
---

To troubleshoot LDAP sources, you can run the command below to run a synchronization in the foreground and see any errors or warnings that might happen directly

```
docker-compose run --rm worker ldap_sync *slug of the source*
```

or, for Kubernetes, run

```
kubectl exec -it deployment/authentik-worker -c authentik -- ak ldap_sync *slug of the source*
```
