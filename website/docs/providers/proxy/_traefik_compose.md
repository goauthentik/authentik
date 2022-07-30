```yaml
version: "3.7"
services:
    traefik:
        image: traefik:v2.2
        container_name: traefik
        volumes:
            - /var/run/docker.sock:/var/run/docker.sock
        ports:
            - 80:80
        command:
            - "--api"
            - "--providers.docker=true"
            - "--providers.docker.exposedByDefault=false"
            - "--entrypoints.web.address=:80"

    authentik-proxy:
        image: ghcr.io/goauthentik/proxy
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
        labels:
            traefik.enable: true
            traefik.port: 9000
            traefik.http.routers.authentik.rule: Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)
            # `authentik-proxy` refers to the service name in the compose file.
            traefik.http.middlewares.authentik.forwardauth.address: http://authentik-proxy:9000/outpost.goauthentik.io/auth/traefik
            traefik.http.middlewares.authentik.forwardauth.trustForwardHeader: true
            traefik.http.middlewares.authentik.forwardauth.authResponseHeaders: X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid,X-authentik-jwt,X-authentik-meta-jwks,X-authentik-meta-outpost,X-authentik-meta-provider,X-authentik-meta-app,X-authentik-meta-version
        restart: unless-stopped

    whoami:
        image: containous/whoami
        labels:
            traefik.enable: true
            traefik.http.routers.whoami.rule: Host(`app.company`)
            traefik.http.routers.whoami.middlewares: authentik@docker
        restart: unless-stopped
```
