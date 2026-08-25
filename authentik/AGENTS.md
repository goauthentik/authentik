# The authentik Django core

`authentik/` is a Django 5 + DRF application split into focused apps. `core/` holds users, applications, and tokens, the models everything else hangs off. `flows/` and `stages/` are the flow engine; `policies/` gates flows, applications, and sources; `sources/` is inbound identity and `providers/` the outbound protocols; `outposts/` manages the Go and Rust outposts. Around those: `brands/` and `tenants/` (theming and multi-tenancy via django-tenants), `blueprints/` (applies the YAML under the top-level `blueprints/`), `events/` (audit log), `tasks/` (the dramatiq layer), `rbac/`, `crypto/`, `enterprise/` (EE-licensed), `api/` and `admin/` (REST surfaces), and `root/` (settings, URLs, ASGI). The layout is discoverable. The rest of this file is the part that isn't.

## Running anything needs Postgres

`manage.py` calls `wait_for_db()` before every command, so without a database everything hangs silently. `docker compose -f scripts/compose.yml up -d` starts Postgres, the S3 stand-in, and Spotlight. There is no Redis anywhere. Cache and the dramatiq task broker are both Postgres.

Local config lives in `local.env.yml` (generate one with `make gen-dev-config`), merged over `authentik/lib/default.yml`. Any key can be overridden per environment variable. `AUTHENTIK_POSTGRESQL__HOST` sets `postgresql.host`, with the double underscore as path separator. `python -m authentik.lib.config <key>` prints the merged value when you're unsure what's winning.

`make run` is `ak allinone`, the Rust binary, which spawns gunicorn and the worker. No UI bundle ships in the repo, so a fresh checkout serves a broken interface until you run `make web-build` once. `make migrate` is not `manage.py migrate`. It runs `lifecycle/migrate.py`, which takes an advisory lock and applies `lifecycle/system_migrations/` first. The `ak` CLI itself is a bash script (`lifecycle/ak`) that forwards unknown subcommands to `manage.py`, which is why `uv run ak makemigrations` works.

## Tests

The supported entrypoint is Django's runner, which is a facade over pytest (`authentik/root/test_runner.py`). **Never run bare `pytest`.** It technically collects, but skips the test-environment setup. The in-process dramatiq broker, forced `tenants.enabled=false`, GeoIP fixtures, and the startup signals all live in the runner, so results from bare pytest are lies.

- `make test` runs the whole suite, and `make test authentik/providers/saml` scopes to a path. A `::`-qualified label makes `make` itself exit non-zero after the tests pass, so for a single test go direct: `uv run manage.py test --keepdb authentik/core/tests/test_users.py::TestUsers::test_x`.
- `--keepdb` translates to pytest's `--reuse-db`. After a model change the reused test database is stale. Drop it (`make dev-drop-db` removes `test_<name>` too) or run once without the flag.
- Test order is randomized by default (pytest-randomly). A test that only passes in file order is broken, not unlucky. Reproduce a CI ordering failure with `--randomly-seed=<n>` from the CI log, and hunt a flake with `--count 20` (pytest-flakefinder).
- `--doctest-modules` is in the pytest addopts, so a `>>>` example in a docstring is a collected test, and a malformed one fails the suite.
- `TypeError: 'datetime' object is not an instance of 'FakeDatetime'` is the known cryptography/freezegun flake class. The test plugin pre-warms against it, but new code holding datetimes across freeze boundaries can reintroduce it.
- Blueprints apply asynchronously via scheduled tasks, so objects a test needs aren't there by default. Decorate with `@apply_blueprint(...)` and `@reconcile_app("authentik_x")` from `authentik/blueprints/tests`.

Size tests to the code. Cover the behavior and the obvious edge cases, don't pad for coverage, and write them against the general mechanism rather than copy-pasting one per model.

## Model and API changes travel together

A model or serializer change is never done until `uv run ak makemigrations` and `make gen` have both run. CI checks pending migrations and diffs the regenerated schema and clients separately, and either one fails the build. Read the generated migration before committing, because makemigrations regularly catches more than you intended. Don't hand-write migrations unless the task is explicitly a data migration or repair, and prefer a blueprint under `blueprints/` over a data migration when the result should be a managed, idempotent object.

**Docstrings on viewsets and serializers are public API documentation.** drf-spectacular lifts them into `schema.yml` as operation and component descriptions, from where they land in three generated clients and the API docs site. Write them for an API consumer or leave them off. A filler `"""FooViewSet"""` becomes a filler description in every client, and touching one shows up as schema diff noise in review.

## Writing code

- Anything user-visible is translatable: `gettext_lazy as _`. Management command help text and errors are the exception, and stay plain English. Never edit `locale/*.po`; strings are extracted.
- Look for the existing helper before writing one. `django.utils` and the auth framework first, then `authentik/lib/` and the app you're in. One concrete trap: event contexts use `authentik.events.utils.model_to_dict`, which returns app/model/pk/name only. Django's own `model_to_dict` would serialize every field, secrets included.
- A new `authentik.*` app wires itself by convention. List it in `SHARED_APPS`/`TENANT_APPS`, subclass `ManagedAppConfig`, and its `settings.py`, `signals.py`, `tasks.py`, and `checks.py` are imported automatically. Startup reconciliation is `@ManagedAppConfig.reconcile_global` / `reconcile_tenant`, not ad-hoc `ready()` code.
- Python is pinned to 3.14 and the code uses 3.14 syntax (PEP 758 bare multi-exception `except` appears in the tree). Don't "fix" it, and don't write for older versions.
- mypy runs `--strict`, but a long `ignore_errors` allowlist in `pyproject.toml` exempts most existing modules. A new module is outside the list and gets the full strict treatment.

## macOS

`lxml` and `xmlsec` must compile against brew's libxml2, or SAML tests fail with linker-level errors. `make core-install` injects the right flags. A bare `uv sync` can quietly leave you with broken wheels.
