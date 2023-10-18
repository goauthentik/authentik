---
title: Full development environment
---

## Requirements

-   Python 3.11
-   Poetry, which is used to manage dependencies
-   Go 1.20
-   Node.js 20
-   PostgreSQL (any recent version will do)
-   Redis (any recent version will do)

## Services Setup

For PostgreSQL and Redis, you can use the `docker-compose.yml` file in `/scripts`.To use these pre-configured database instances, navigate to the `/scripts` directory in your local copy of the authentik git repo, and run `docker compose up -d`.
You can also use a native install, if you prefer.

:::info
If you use locally installed databases, the PostgreSQL credentials given to authentik should have permissions for `CREATE DATABASE` and `DROP DATABASE`, because authentik creates a temporary database for tests.
:::

## Backend Setup

:::info
Depending on your platform, some native dependencies might be required. On macOS, run `brew install libxmlsec1 libpq`, and for the CLI tools `brew install postgresql redis node@20`
:::

:::info
As long as [this issue](https://github.com/xmlsec/python-xmlsec/issues/252) about `libxmlsec-1.3.0` is open, a workaround is required to install a compatible version of `libxmlsec1` with brew, see [this comment](https://github.com/xmlsec/python-xmlsec/issues/254#issuecomment-1612005910).
:::

1. Create an isolated Python environment. To create the environment and install dependencies, run the following commands in the same directory as your local authentik git repository:

```shell
poetry shell # Creates a python virtualenv, and activates it in a new shell
make install # Installs all required dependencies for Python and Javascript, including development dependencies
```

2. Configure authentik to use the local databases using a local config file. To generate this file, run the following command in the same directory as your local authentik git repository:

```shell
make gen-dev-config # Generates a local config file
```

Generally speaking, authentik is a Django application, ran by gunicorn, proxied by a Go application. The Go application serves static files.

Most functions and classes have type-hints and docstrings, so it is recommended to install a Python Type-checking Extension in your IDE to navigate around the code.

Before committing code, run the following commands in the same directory as your local authentik git repository:

```shell
make lint # Ensures your code is well-formatted
make gen # Generates an updated OpenAPI Docs for any changes you make
```

:::info
Linting also requires `pyright`, which is installed in the `web/` folder to make dependency management easier.
:::

## Frontend Setup

By default, no compiled bundle of the frontend is included so this step is required even if you're not developing for the UI.

To build the UI once, run the following command in the same directory as your local authentik git repository:

```shell
make web-build # Builds the UI once
```

If you want to live-edit the UI, you can run the following command in the same directory as your local authentik git repository instead, which will immediately update the UI with any changes you make so you can see the results in real time without needing to rebuild:

```shell
make web-watch # Updates the UI with any changes you make
```

To format the frontend code, run the following command in the same directory as your authentik git repository:

```shell
make web # Formats the frontend code
```

## Running authentik

Now that the backend and frontend have been setup and built, you can start authentik by running the following command in the same directory as your local authentik git repository:

```shell
ak server # Starts authentik server
```

And now, authentik should now be accessible at `http://localhost:9000`.

:::info
To define a password for the default admin (called **akadmin**), you can manually enter the `/if/flow/initial-setup/` path in the browser address bar to launch the initial flow.
Example: http://localhost:9000/if/flow/initial-setup/
:::
