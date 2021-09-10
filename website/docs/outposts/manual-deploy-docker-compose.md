---
title: Manual Outpost deployment in docker-compose
---

To deploy an outpost with docker-compose, use this snippet in your docker-compose file.

You can also run the outpost in a separate docker-compose project, you just have to ensure that the outpost container can reach your application container.

```yaml
version: "3.5"

services:
  authentik_proxy:
    image: ghcr.io/goauthentik/proxy:2021.8.5
    ports:
      - 9000:9000
      - 9443:9443
    environment:
      AUTHENTIK_HOST: https://your-authentik.tld
      AUTHENTIK_INSECURE: "false"
      AUTHENTIK_TOKEN: token-generated-by-authentik
      # Starting with 2021.10, you can optionally set this too
      # when authentik_host for internal communication doesn't match the public URL
      # AUTHENTIK_HOST_BROWSER: https://external-domain.tld
  # Or, for the LDAP Outpost
  authentik_proxy:
    image: ghcr.io/goauthentik/ldap:2021.8.5
    ports:
      - 389:3389
    environment:
      AUTHENTIK_HOST: https://your-authentik.tld
      AUTHENTIK_INSECURE: "false"
      AUTHENTIK_TOKEN: token-generated-by-authentik
```
