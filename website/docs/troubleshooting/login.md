---
title: I can't log in to authentik
---

In case you can't login anymore, perhaps due to an incorrectly configured stage or a failed flow import, you can create a recovery key.

:::caution
This recovery key will give whoever has the link direct access to your instances. Keep this key safe.
:::

To create the key, run the following command:

```
docker-compose run --rm server create_recovery_key 10 akadmin
```

or, for Kubernetes, run

```
kubectl exec -it deployment/authentik-worker -c authentik -- ak create_recovery_key 10 akadmin
```

This will output a link, that can be used to instantly gain access to authentik as the user specified above. The link is valid for amount of years specified above, in this case, 10 years.
