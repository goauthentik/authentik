
```yaml
version: '3.7'
services:
  traefik:
    image: traefik:v2.2
    container_name: traefik
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      traefik.enable: true
      traefik.http.routers.api.rule: Host(`traefik.example.com`)
      traefik.http.routers.api.entrypoints: https
      traefik.http.routers.api.service: api@internal
      traefik.http.routers.api.tls: true
    ports:
      - 80:80
      - 443:443
    command:
      - '--api'
      - '--log=true'
      - '--log.level=DEBUG'
      - '--log.filepath=/var/log/traefik.log'
      - '--providers.docker=true'
      - '--providers.docker.exposedByDefault=false'
      - '--entrypoints.http=true'
      - '--entrypoints.http.address=:80'
      - '--entrypoints.http.http.redirections.entrypoint.to=https'
      - '--entrypoints.http.http.redirections.entrypoint.scheme=https'
      - '--entrypoints.https=true'
      - '--entrypoints.https.address=:443'

  authentik_proxy:
    image: goauthentik.io/proxy:2021.5.1
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
      traefik.http.routers.authentik.rule: Host(`*external host that you configured in authentik*`) && PathPrefix(`/akprox/`)
      traefik.http.routers.authentik.entrypoints: https
      traefik.http.routers.authentik.tls: true
      traefik.http.middlewares.authentik.forwardauth.address: http://authentik_proxy:9000/akprox/auth/traefik
      traefik.http.middlewares.authentik.forwardauth.trustForwardHeader: true
      traefik.http.middlewares.authentik.forwardauth.authResponseHeaders: Set-Cookie,X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
    restart: unless-stopped

  whoami:
    image: containous/whoami
    labels:
      traefik.enable: true
      traefik.http.routers.whoami.rule: Host(`*external host that you configured in authentik*`)
      traefik.http.routers.whoami.entrypoints: https
      traefik.http.routers.whoami.tls: true
      traefik.http.routers.whoami.middlewares: authentik@docker
    restart: unless-stopped
```
