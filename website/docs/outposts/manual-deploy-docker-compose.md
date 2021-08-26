---
title: Manual Outpost deployment in docker-compose
---

To deploy an outpost with docker-compose, use this snippet in your docker-compose file.

You can also run the outpost in a separate docker-compose project, you just have to ensure that the outpost container can reach your application container.

```yaml
version: "3.5"

services:
  authentik_proxy:
    image: ghcr.io/goauthentik/proxy:2021.8.1
    ports:
      - 4180:4180
      - 4443:4443
    environment:
      AUTHENTIK_HOST: https://your-authentik.tld
      AUTHENTIK_INSECURE: "false"
      AUTHENTIK_TOKEN: token-generated-by-authentik
  # Or, for the LDAP Outpost
  authentik_proxy:
    image: ghcr.io/goauthentik/ldap:2021.8.1
    ports:
      - 389:3389
    environment:
      AUTHENTIK_HOST: https://your-authentik.tld
      AUTHENTIK_INSECURE: "false"
      AUTHENTIK_TOKEN: token-generated-by-authentik
```
