---
title: Frontend-only development environment
---

If you want to only make changes on the UI, you don't need a backend running from source. You can user the docker-compose install with a few customizations.

1. Clone the git repo from https://github.com/goauthentik/authentik
2. In the cloned repository, follow the docker-compose installation instructions [here](/docs/installation/docker-compose)
3. Add the following entry to your `.env` file:

    ```
    AUTHENTIK_IMAGE=beryju.org/authentik/server
    AUTHENTIK_TAG=gh-next
    AUTHENTIK_OUTPOSTS__DOCKER_IMAGE_BASE=beryju.org/authentik/outpost-%(type)s:gh-next
    ```

    This will cause authentik to use the beta images.

4. Create a `local.env.yml` file to tell authentik to use local files instead of the bundled ones:

    ```yaml
    log_level: debug
    web:
      load_local_files: true
    ```

5. Add this volume mapping to your compose file

    ```yaml
    version: '3.2'

    services:
      # [...]
      server:
        # [...]
        volumes:
          - ./web:/web
          - ./local.env.yml:/local.env.yml
    ```

    This makes the local web files and the config file available to the authentik server.

6. Run `docker-compose up -d` to apply those changes to your containers.
7. Run `make gen-web` in the project root directory to generate the API Client used by the web interfaces
8. `cd web`
9. Run `npm i` and then `npm run watch` to start the build process.

You can now access authentik on http://localhost:9000 (or https://localhost:9443).

You might also want to complete the initial setup under `/if/flow/initial-setup/`.
