---
title: Full development environment
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

## Requirements

- [Python](https://www.python.org/) 3.12
- [Poetry](https://python-poetry.org/), which is used to manage dependencies
    - Poetry 2.0 or higher also requires the [poetry-plugin-shell](https://github.com/python-poetry/poetry-plugin-shell) extension.
- [Go](https://go.dev/) 1.23 or newer
- [Node.js](https://nodejs.org/en) 21 or newer
- [PostgreSQL](https://www.postgresql.org/) 14 or newer
- [Redis](https://redis.io/) (any recent version will do)
- [Docker](https://www.docker.com/) (Community Edition will do)

## Services Setup

For PostgreSQL and Redis, you can use the `docker-compose.yml` file in `/scripts`.To use these pre-configured database instances, navigate to the `/scripts` directory in your local copy of the authentik git repo, and run `docker compose up -d`.
You can also use a native install, if you prefer.

:::info
If you use locally installed databases, the PostgreSQL credentials given to authentik should have permissions for `CREATE DATABASE` and `DROP DATABASE`, because authentik creates a temporary database for tests.
:::

## Backend Setup

:::info
Depending on your platform, some native dependencies might be required.

<Tabs
defaultValue={ (ExecutionEnvironment.canUseDOM) ? (() => {
const ua = window.navigator.userAgent.toLowerCase();
return ["linux", "windows", "mac"].find((p) => ua.includes(p)) || "mac";
})() : "mac" }

values={[
{label: "macOS", value: "mac"},
{label: "Linux", value: "linux"},
{label: "Windows", value: "windows"},
]}>

  <TabItem value="mac">
    To install the native dependencies on macOS, run:
    
    ```sh
    $ pip install poetry poetry-plugin-shell
    $ brew install libxmlsec1 libpq krb5   # Required development libraries,
    $ brew install postgresql redis node@22 golangci-lint   # Required CLI tools
  ```

  </TabItem>

  <TabItem value="linux">
  To install native dependencies on Debian or Ubuntu, run:

```sh
$ pip install poetry poetry-plugin-shell
$ sudo apt-get install  libgss-dev krb5-config libkrb5-dev postgresql-server-dev-all
$ sudo apt-get install postresql redis
```

Adjust your needs as required for other distributions such as Red Hat, SUSE, or Arch.

Install golangci-lint locally [from the site
instructions](https://golangci-lint.run/welcome/install/#other-ci).

  </TabItem>

<TabItem value="windows">[We request community input on running the full dev environment on Windows]</TabItem>

</Tabs>

:::

1. Create an isolated Python environment. To create the environment and install dependencies, run the following commands in the same directory as your local authentik git repository:

```shell
poetry shell   # Creates a python virtualenv, and activates it in a new shell
make install   # Installs all required dependencies for Python and Javascript, including development dependencies
```

2. Configure authentik to use the local databases using a local config file. To generate this file, run the following command in the same directory as your local authentik git repository:

```shell
make gen-dev-config   # Generates a local config file
```

Generally speaking, authentik is a Django application, ran by gunicorn, proxied by a Go application. The Go application serves static files.

Most functions and classes have type-hints and docstrings, so it is recommended to install a Python Type-checking Extension in your IDE to navigate around the code.

## Frontend Setup

By default, no compiled bundle of the frontend is included so this step is required even if you're not developing for the UI.

The UI requires the authentik API files for Typescript be built and installed:

```
$ make migrate   # On a fresh install, ensures the API schema file is available
$ make gen       # Generates the API based on the schema file
```

If you make changes to the authentik API, you must re-run `make gen` so that the corresponding
changes are made to the API library that is used by the UI.

To build the UI once, run the following command in the same directory as your local authentik git repository:

```shell
make web-build   # Builds the UI once
```

If you want to live-edit the UI, you can run the following command in the same directory as your local authentik git repository instead, which will immediately update the UI with any changes you make so you can see the results in real time without needing to rebuild:

```shell
make web-watch   # Updates the UI with any changes you make
```

To format the frontend code, run the following command in the same directory as your authentik git repository:

```shell
make web   # Formats the frontend code
```

## Running authentik

Now that the backend and frontend have been setup and built, you can start authentik by running the following command in the same directory as your local authentik git repository:

```shell
ak server   # Starts authentik server
```

And now, authentik should now be accessible at `http://localhost:9000`.

:::info
To define a password for the default admin (called **akadmin**), you can manually enter the `/if/flow/initial-setup/` path in the browser address bar to launch the initial flow. Example: http://localhost:9000/if/flow/initial-setup/.

In case of issues in this process, feel free to use `make dev-reset` which drops and restores the Authentik PostgreSQL instance to a "fresh install" state.
:::

## Submitting Pull Requests

Before submitting a pull request, run the following commands in the same directory as your local authentik git repository:

```shell
make lint   # Ensures your code is well-formatted
make gen    # Generates an updated OpenAPI Docs for any changes you make
make web    # Formats the front-end code
```
