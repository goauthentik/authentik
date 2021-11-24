---
title: Docker
---

The docker integration will automatically deploy and manage outpost containers using the Docker HTTP API.

This integration has the advantage over manual deployments of automatic updates (whenever authentik is updated, it updates the outposts), and authentik can (in a future version) automatically rotate the token that the outpost uses to communicate with the core authentik server.

The following outpost settings are used:

- `object_naming_template`: Configures how the container is called
- `container_image`: Optionally overwrites the standard container image (see [Configuration](../../installation/configuration.md) to configure the global default)
- `docker_network`: The docker network the container should be added to. This needs to be modified if you plan to connect to authentik using the internal hostname.
- `docker_map_ports`: Enable/disable the mapping of ports. When using a proxy outpost with traefik for example, you might not want to bind ports as they are routed through traefik.

The container is created with the following hardcoded properties:

- Labels

    - `io.goauthentik.outpost-uuid`: Used by authentik to identify the container, and to allow for name changes.

    Additionally, the proxy outposts have the following extra labels to add themselves into traefik automatically.

    - `traefik.enable`: "true"
    - `traefik.http.routers.ak-outpost-<outpost-id>-router.rule`: `Host(...)`
    - `traefik.http.routers.ak-outpost-<outpost-id>-router.service`: `ak-outpost-<outpost-id>-service`
    - `traefik.http.routers.ak-outpost-<outpost-id>-router.tls`: "true"
    - `traefik.http.services.ak-outpost-<outpost-id>-service.loadbalancer.healthcheck.path`: "/akprox/ping"
    - `traefik.http.services.ak-outpost-<outpost-id>-service.loadbalancer.healthcheck.port`: "9300"
    - `traefik.http.services.ak-outpost-<outpost-id>-service.loadbalancer.server.port`: "9000"

## Permissions

To minimise the potential risks of mapping the docker socket into a container/giving an application access to the docker API, many people use Projects like [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy). authentik requires these permissions from the docker API:

- Images/Pull: authentik tries to pre-pull the custom image if one is configured, otherwise falling back to the default image.
- Containers/Read: Gather infos about currently running container
- Containers/Create: Create new containers
- Containers/Kill: Cleanup during upgrades
- Containers/Remove: Removal of outposts

## Remote hosts

To connect remote hosts, you can follow this Guide from Docker [Use TLS (HTTPS) to protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/#use-tls-https-to-protect-the-docker-daemon-socket) to configure Docker.

Afterwards, create two Certificate-keypairs in authentik:

- `Docker CA`, with the contents of `~/.docker/ca.pem` as Certificate
- `Docker Cert`, with the contents of `~/.docker/cert.pem` as Certificate and `~/.docker/key.pem` as Private key.

Create an integration with `Docker CA` as *TLS Verification Certificate* and `Docker Cert` as *TLS Authentication Certificate*.
