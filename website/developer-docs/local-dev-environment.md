---
title: Getting started
slug: /
---

## Backend

To create a local development setup for authentik, you need the following:

- Python 3.9
- pipenv, which is used to manage dependencies, and can be installed with `pip install pipenv`
- PostgreSQL (any recent version will do)
- Redis (any recent version will do)

For PostgreSQL and Redis, you can use the docker-compose file in `scripts/`. You can also use a native install, if you prefer.

To configure authentik to use the local databases, create a file in the authentik directory called `local.env.yml`, with the following contents

```yaml
debug: true
postgresql:
  user: postgres

log_level: debug
```

Afterwards, you can start authentik by running `./manage.py runserver`. Generally speaking, authentik is a Django application.

Most functions and classes have type-hints and docstrings, so it is recommended to install a Python Type-checking Extension in your IDE to navigate around the code.

Before committing code, run `make lint` to ensure your code is formatted well. This also requires `pyright`, which can be installed with npm.

Run `make gen` to run all unittests and generated an updated swagger document for any changes you made.

## Frontend

By default, no transpiled bundle of the frontend is included. To build the UI, you need Node 12 or newer.

The Frontend also uses a generated API client to talk with the backend. To generate this client, [openapitools/openapi-generator-cli](https://github.com/OpenAPITools/openapi-generator) is used.

If you want to generate the client without installing anything, run this command:

```shell
make gen-web
```

To build the UI, run these commands:

```
cd web/
npm i
npm run build
```

If you want to make changes to the UI, run `npm run watch` instead.

To ensure the code is formatted well, run `npx eslint . --fix` and `npm run lit-analyse`.
