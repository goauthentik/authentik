---
title: Setting up a local dev environment
---

## Backend

To create a local development setup for passbook, you need the following:

- Python 3.9
- pipenv, which is used to manage dependencies, and can be installed with `pip install pipenv`
- PostgreSQL (any recent version will do)
- Redis (any recent version will do)

For PostgreSQL and Redis, you can use the docker-compose file in `scripts/`. You can also use a native install, if you prefer.

To configure passbook to use the local databases, create a file in the passbook directory called `local.env.yml`, with the following contents

```yaml
debug: true
postgresql:
  user: postgres

log_level: debug
```

Afterwards, you can start passbook by running `./manage.py runserver`. Generally speaking, passbook is a Django application.

Most functions and classes have type-hints and docstrings, so it is recommended to install a Python Type-checking Extension in your IDE to navigate around the code.

## Frontend

By default, no transpiled bundle of the frontend is included. To build the UI, you need Node 12 or newer.

To build the UI, run these commands:

```
cd web/
npm i
npm run build
```

If you want to make changes to the UI, run `npm run watch` instead.
