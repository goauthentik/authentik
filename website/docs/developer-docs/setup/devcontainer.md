---
title: Devcontainer development environment
sidebar_label: Devcontainer development
tags:
    - development
    - contributor
    - devcontainer
    - docker
---

If you prefer a containerized development environment with all dependencies pre-configured, you can use the devcontainer setup. This provides a fully isolated development environment that runs inside Docker. The devcontainer mounts your local workspace into the container, so changes to files are reflected immediately.

### Prerequisites

- [Docker](https://www.docker.com/) (Latest Community Edition or Docker Desktop)
- [Visual Studio Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Alternatively, you can use any IDE or editor that supports the [devcontainer specification](https://containers.dev/).

### Instructions

1. Clone the Git repo to your development machine and navigate to the authentik directory.

    ```shell
    git clone https://github.com/goauthentik/authentik
    cd authentik
    ```

2. Open the repository in Visual Studio Code.

    ```shell
    code .
    ```

3. When prompted, click "Reopen in Container" or run the command "Dev Containers: Reopen in Container" from the command palette (Ctrl+Shift+P / Cmd+Shift+P).

4. VS Code will build the devcontainer image and start the container. This may take several minutes on the first run.

5. Once the container is running, all development tools and dependencies will be available inside the container environment.

### What's included

The devcontainer provides:

- Pre-configured development environment with all required dependencies
- Python, Go, and Node.js development tools
- PostgreSQL database
- All necessary system packages

### Running authentik

After the devcontainer starts, you can run authentik using the standard development commands:

Start the server:

```shell
make run-server
```

In a separate terminal, start the worker:

```shell
make run-worker
```

For frontend development:

```shell
make web-watch
```

authentik will be accessible at http://localhost:9000.

### Initial setup

To set a password for the default admin user (**akadmin**):

1. Navigate to http://localhost:9000/if/flow/initial-setup/ in your browser.
2. Follow the prompts to set up your admin account.

### Hot-reloading

When `AUTHENTIK_DEBUG` is set to `true` (the default for the development environment), the authentik server automatically reloads whenever changes are made to the code. However, due to instabilities in the reloading process of the worker, that behavior is turned off for the worker. You can enable code reloading in the worker by manually running `uv run ak worker --watch`.

## End-to-End (E2E) Setup

Start the E2E test services with the following command:

```shell
docker compose -f tests/e2e/docker-compose.yml up -d
```

You can then view the Selenium Chrome browser via http://localhost:7900/ using the password: `secret`.

Alternatively, you can connect directly via VNC on port `5900` using the password: `secret`.

:::info
When using Docker Desktop, host networking needs to be enabled via **Docker Settings** > **Resources** > **Network** > **Enable host networking**.
:::

## 6. Contributing code

### Before submitting a pull request

Ensure your code meets our quality standards by running:

1. **Code linting**:

    ```shell
    make lint-fix
    make lint
    ```

2. **Generate updated API documentation**:

    ```shell
    make gen
    ```

3. **Format frontend code**:

    ```shell
    make web
    ```

4. **Run tests**:

    ```shell
    make test
    ```

You can run all these checks at once with:

```shell
make all
```

### Submitting your changes

After your code passes all checks, submit a pull request on [GitHub](https://github.com/goauthentik/authentik/pulls). Be sure to:

- Provide a clear description of your changes
- Reference any related issues
- Follow our code style guidelines
- Update any related documentation
- Include tests for your changes where appropriate

Thank you for contributing to authentik!
