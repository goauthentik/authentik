---
title: Frontend-only development environment
---

If you want to only make changes on the UI, you don't need a backend running from source. You can user the docker-compose install with a few customizations.

### Prerequisites

-   Node (any recent version should work, we use 20.x to build)
-   Make (again, any recent version should work)
-   Docker and docker-compose

:::info
Depending on platform, some native dependencies might be required. On macOS, run `brew install node@20`, and for docker `brew install --cask docker`
:::

### Instructions

1. Clone the git repo from https://github.com/goauthentik/authentik
2. In the cloned repository, follow the docker-compose installation instructions [here](/docs/installation/docker-compose)
3. Add the following entry to your `.env` file:

    ```
    AUTHENTIK_IMAGE=ghcr.io/goauthentik/dev-server
    AUTHENTIK_TAG=gh-next
    AUTHENTIK_OUTPOSTS__CONTAINER_IMAGE_BASE=ghcr.io/goauthentik/dev-%(type)s:gh-next
    AUTHENTIK_LOG_LEVEL=debug
    ```

    This will cause authentik to use the beta images.

4. Add this volume mapping to your compose file

    ```yaml
    version: "3.2"

    services:
        # [...]
        server:
            # [...]
            volumes:
                - ./web:/web
                - ./local.env.yml:/local.env.yml
    ```

    This makes the local web files and the config file available to the authentik server.

5. Run `docker-compose up -d` to apply those changes to your containers.
6. `cd web`
7. Run `npm i` and then `npm run watch` to start the build process.

You can now access authentik on http://localhost:9000 (or https://localhost:9443).

You might also want to complete the initial setup under `/if/flow/initial-setup/`.
