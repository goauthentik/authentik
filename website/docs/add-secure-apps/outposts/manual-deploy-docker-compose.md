---
title: Manual Outpost deployment in Docker Compose
---

To deploy an outpost with Docker Compose, use the appropriate snippet from the options below and add it to your Compose file.

You can also run the outpost in a separate Compose project, you just have to ensure that the outpost container can reach your application container.

### Proxy outpost

```yaml
services:
    authentik_proxy:
        image: ghcr.io/goauthentik/proxy
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 9000:9000
            - 9443:9443
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
            # Optional setting to be used when `authentik_host` for internal communication doesn't match the public URL.
            # AUTHENTIK_HOST_BROWSER: https://external-domain.tld
```

### LDAP outpost

```yaml
services:
    authentik_ldap:
        image: ghcr.io/goauthentik/ldap
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 389:3389
            - 636:6636
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```

### RAC outpost

```yaml
services:
    rac_outpost:
        image: ghcr.io/goauthentik/rac
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```

### RADIUS outpost

```yaml
services:
    radius_outpost:
        image: ghcr.io/goauthentik/radius
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 1812:1812/udp
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```
