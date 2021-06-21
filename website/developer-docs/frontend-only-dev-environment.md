---
title: Frontend-only development environment
---

If you want to only make changes on the UI, you don't need a backend running from source. You can user the docker-compose install with a few customizations.

1. Clone the git repo from https://github.com/goauthentik/authentik
2. In the cloned repository, follow the docker-compose installation instructions [here](../../docs/installation/docker-compose)
3. Add the following entry to your `.env` file:

    ```
    AUTHENTIK_WEB__LOAD_LOCAL_FILES=true
    ```

    This will cause authentik to load static files from a folder and ignore the bundeled files.

4. Add this volume mapping to your compose file

    ```yaml
    version: '3.2'

    services:
        # [...]
        server:
            # [...]
            volumes:
            - ./web:/web
    ```

    This makes the local web files available to the authentik server.

5. Run `docker-compose up -d` to apply those changes to your containers.
6. Run `make gen-web` in the project root directory to generate the API Client used by the web interfaces
7. `cd web`
8. Run `npm i` and then `npm run watch` to start the build process.

You can now access authentik on http://localhost:9000 (or https://localhost:9443).

You might also want to complete the initial setup under `/if/flow/initial-setup/`.
