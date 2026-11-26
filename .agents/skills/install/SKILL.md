---
name: install
description: >
    Install and run authentik for real use (self-hosting) with Docker Compose, Kubernetes
    (Helm), or AWS, and get to the first admin login. Use when someone asks "how do I set
    up authentik", "install authentik", "run authentik on my server", "deploy authentik to
    Kubernetes", "try authentik with Docker", or "I can't reach the initial setup page".
    If they want to work on authentik's code, use dev-environment instead.
---

# Install authentik

## Purpose

"Set up authentik" means one of two things. Ask, or infer from context:

- **Run authentik** as the sign-in for your apps (homelab, company, evaluation): this skill.
- **Develop authentik** from this checkout (change code, run tests): the dev-environment
  skill. Its `make` targets build a development stack for working on the code. A
  deployment follows the published guides below.

The published guides hold the authoritative steps. This skill picks the right one and adds the
traps. Guides live in `website/docs/install-config/` and are published at
<https://docs.goauthentik.io/install-config/>.

## Pick an install method

| Situation                             | Guide                                                   |
| ------------------------------------- | ------------------------------------------------------- |
| One host, evaluation, homelab, small  | `install/docker-compose.mdx` (Docker or Podman Compose) |
| A Kubernetes cluster you already run  | `install/kubernetes.mdx` (Helm chart)                   |
| AWS with CloudFormation               | `install/aws.mdx`                                       |
| Two or more replicas, failover        | `high-availability.mdx`, after one of the above         |
| No internet access                    | `air-gapped.mdx`                                        |
| Unattended install (CI, provisioning) | `automated-install.mdx`                                 |

Requirements for all methods: at least 2 CPU cores and 2 GB of RAM.

## Workflow (Docker Compose)

Steps are tagged: `[shell]` run a command on the host, `[verify]` check before moving on.
Work in an empty directory outside this repository.

1. **[shell]** Download the Compose file: `curl -O https://docs.goauthentik.io/compose.yml`.
2. **[shell]** Generate secrets into `.env`. Do this only on a fresh install: regenerating
   them later locks you out of the existing database.

    ```shell
    echo "PG_PASS=$(openssl rand -base64 36 | tr -d '\n')" >> .env
    echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n')" >> .env
    ```

3. **[shell]** Optional: set ports (`COMPOSE_PORT_HTTP`, `COMPOSE_PORT_HTTPS`) and email
   in `.env`, as the guide describes.
4. **[shell]** `docker compose pull && docker compose up -d`.
5. **[verify]** `docker compose ps` shows the containers healthy. The first start runs
   migrations and takes a minute or two.
6. **[verify]** Open `http://<host>:9000/` and set the **akadmin** password when prompted.

For Kubernetes, follow `install/kubernetes.mdx`: generate the secrets, write
`values.yaml`, then `helm upgrade --install authentik authentik/authentik -f values.yaml`.

After the first login, `first-steps/` walks through adding the first application.

## Gotchas

- **Start at the root URL.** A direct visit to `/if/flow/initial-setup/` shows "Access
  denied" by design. If setup still fails, restart the containers. If that doesn't help,
  set the password directly with `docker compose exec server ak changepassword akadmin`
  (see `troubleshooting/login.mdx`).
- **Don't mount `/etc/timezone` or `/etc/localtime`** into the containers. authentik runs
  in UTC and the UI localizes times. A different container time zone breaks OAuth and SAML.
- **The Compose file pins a version.** To upgrade, download a new `compose.yml`, then
  follow the version's upgrade notes in the release notes (`upgrade.mdx`).
- **PostgreSQL passwords over 99 characters fail.** The generator above stays under that.
- **Behind a reverse proxy,** follow `reverse-proxy.mdx` for the headers and WebSocket
  settings. The proxy must speak HTTP/1.1 or newer and pass the `Host` and WebSocket
  upgrade headers, or outposts and host checks fail.
- **Locked out of akadmin?** Create a recovery key (`troubleshooting/login.mdx`). With
  Compose: `docker compose run --rm server create_recovery_key 10 akadmin`.
