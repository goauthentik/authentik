---
title: Debugging authentik
---

This page describes how to debug different components of an authentik instance, running either in production or in a development setup. To learn more about the structure of authentik, refer to our [architecture documentation](../../core/architecture.md).

## authentik Server & Worker (Python)

The majority of the authentik codebase is in Python, running in Gunicorn for the server and Dramatiq for the worker. These instructions show how this code can be debugged/inspected. The local debugging setup requires a setup as described in [Full development environment](./full-dev-environment.mdx)

Note that authentik uses [debugpy](https://github.com/microsoft/debugpy), which relies on the "Debug Adapter Protocol" (DAP). These instructions demonstrate debugging using [Visual Studio Code](https://code.visualstudio.com/), however they should be adaptable to other editors that support DAP.

To enable the debugging server, set the environment variable `AUTHENTIK_DEBUGGER` to `true`. This will launch the debugging server (by default on port _9901_).

With this setup in place, you can set Breakpoints in VS Code. To connect to the debugging server, run the command `> Debug: Start Debugging" in VS Code.

![](./debug_vscode.png)

:::info
Note that due to the Python debugger for VS Code, when a Python file in authentik is saved and the Django process restarts, you must manually reconnect the Debug session. Automatic re-connection is not supported for the Python debugger (see [here](https://github.com/microsoft/vscode-python/issues/19998) and [here](https://github.com/microsoft/vscode-python/issues/1182)).
:::

#### Debug the server or the worker

Whichever process is first started listens on port `9901`. Additional processes started after that will then try to listen on the same port, which will fail, and will simply not start the debugger in that case.

#### Debugging in containers

When debugging an authentik instance running in containers, there are some additional steps that need to be taken in addition to the steps above.

A local clone of the authentik repository is required to be able to set breakpoints in the code. The locally checked out repository must be on the same version/commit as the authentik version running in the containers. To checkout version 2024.12.3 for example, you can run `git checkout version/2024.12.3`.

The debug port needs to be accessible on the local machine. By default, this is port 9901. Additionally, the container being debugged must be started as `root`, because additional dependencies need to be installed on startup.

When running in Docker Compose, a file `docker-compose.override.yml` can be created next to the authentik docker-compose.yml file to expose the port, change the user, and enable debug mode.

```yaml
services:
    # Replace `server` with `worker` to debug the worker container.
    server:
        user: root
        healthcheck:
            disable: true
        environment:
            AUTHENTIK_DEBUGGER: "true"
            AUTHENTIK_LOG_LEVEL: "debug"
        ports:
            - 9901:9901
```

After re-creating the containers with `AUTHENTIK_DEBUGGER` set to `true` and the port mapped, the steps are identical to the steps above.

If the authentik instance is running on a remote server, the `.vscode/launch.json` file needs to be adjusted to point to the IP of the remote server. Alternatively, it is also possible to forward the debug port via an SSH tunnel, using `-L 9901:127.0.0.1:9901`.

## authentik Server / Outposts (Golang)

Outposts, as well as some auxiliary code of the authentik server, are written in Go. These components can be debugged using standard Golang tooling, such as [Delve](https://github.com/go-delve/delve).
