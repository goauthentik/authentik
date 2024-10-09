---
title: Manual Outpost deployment in docker-compose
---

To deploy an outpost with docker-compose, use this snippet in your docker-compose file.

You can also run the outpost in a separate docker-compose project, you just have to ensure that the outpost container can reach your application container.

### Proxy outpost

```yaml
services:
    authentik_proxy:
        image: ghcr.io/goauthentik/proxy
        # Optionally specify which networks the container should be
        # might be needed to reach the core authentik server
        # networks:
        #   - foo
        ports:
            - 9000:9000
            - 9443:9443
        environment:
            AUTHENTIK_HOST: https://your-authentik.tld
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
            # Starting with 2021.9, you can optionally set this too
            # when authentik_host for internal communication doesn't match the public URL
            # AUTHENTIK_HOST_BROWSER: https://external-domain.tld
```

### LDAP outpost

```yaml
services:
    authentik_ldap:
        image: ghcr.io/goauthentik/ldap
        # Optionally specify which networks the container should be
        # might be needed to reach the core authentik server
        # networks:
        #   - foo
        ports:
            - 389:3389
            - 636:6636
        environment:
            AUTHENTIK_HOST: https://your-authentik.tld
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```

### RADIUS outpost

```yaml
services:
    radius_outpost:
        image: ghcr.io/goauthentik/radius
        # Optionally specify which networks the container should be
        # might be needed to reach the core authentik server
        # networks:
        #   - foo
        ports:
            - 1812:1812/udp
        environment:
            AUTHENTIK_HOST: https://your-authentik.tld
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```
