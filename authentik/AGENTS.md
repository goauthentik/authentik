# authentik/ — the Django core

Django 5 + DRF, split into focused apps: `core/` (users, applications, tokens — the models everything hangs off), `flows/` + `stages/` (the flow engine), `policies/` (gates flows, applications, sources), `sources/` (inbound identity), `providers/` (outbound protocols), `outposts/` (manages the Go/Rust outposts), `brands/` + `tenants/` (theming, multi-tenancy via django-tenants), `blueprints/` (applies the YAML under the top-level `blueprints/`), `events/` (audit log), `tasks/` (dramatiq layer), `rbac/`, `crypto/`, `enterprise/` (EE-licensed), `api/` + `admin/` (REST surfaces), `root/` (settings, URLs, ASGI).

## Running

- **Postgres must be running first.** `manage.py` calls `wait_for_db()` before every command, so everything hangs silently without it. Start dev services with `docker compose -f scripts/compose.yml up -d` (Postgres, S3 stand-in, Spotlight).
- There is no Redis. Cache and the dramatiq broker are both Postgres.
- Local config: `local.env.yml` (create with `make gen-dev-config`), merged over `authentik/lib/default.yml`. Env override syntax: `AUTHENTIK_POSTGRESQL__HOST` sets `postgresql.host` (double underscore = path separator). `python -m authentik.lib.config <key>` prints the merged value.
- `make run` = `ak allinone`: the Rust binary, which spawns gunicorn and the worker.
- No UI bundle ships in the repo — run `make web-build` once or a fresh checkout serves a broken interface.
- `make migrate` is not `manage.py migrate`: it runs `lifecycle/migrate.py`, which takes an advisory lock and applies `lifecycle/system_migrations/` first.
- The `ak` CLI is a bash script (`lifecycle/ak`) that forwards unknown subcommands to `manage.py` — hence `uv run ak makemigrations`.

## Tests

```bash
make test                                # full suite
make test authentik/providers/saml       # scope to a path
uv run manage.py test --keepdb authentik/core/tests/test_users.py::TestUsers::test_x
                                         # single test — `make test` with `::` exits non-zero after passing
uv run manage.py test --keepdb --count 20 <label>          # flake hunt (pytest-flakefinder)
uv run manage.py test --keepdb --randomly-seed=<n> <label> # reproduce a CI ordering failure
```

- **Never run bare `pytest`.** The Django runner (`authentik/root/test_runner.py`) is a facade over pytest and sets up the test environment: in-process dramatiq broker, `tenants.enabled=false`, GeoIP fixtures, startup signals. Bare pytest skips all of it and gives wrong results.
- `--keepdb` maps to pytest's `--reuse-db`. After a model change the reused test DB is stale — `make dev-drop-db` (also drops `test_<name>`) or run once without the flag.
- Test order is randomized (pytest-randomly). A test that only passes in file order is broken.
- `--doctest-modules` is in the pytest addopts: a `>>>` example in any docstring is a collected test.
- `TypeError: 'datetime' object is not an instance of 'FakeDatetime'` = the known cryptography/freezegun flake class. The test plugin pre-warms against it; holding datetimes across freeze boundaries reintroduces it.
- Blueprints apply asynchronously via scheduled tasks, so objects a test needs aren't there by default. Use `@apply_blueprint(...)` and `@reconcile_app("authentik_x")` from `authentik/blueprints/tests`.
- Size tests to the code: cover behavior and obvious edge cases, don't pad for coverage, test the general mechanism instead of copy-pasting one test per model.

## Migrations and the API schema

- A model or serializer change is done only after both `uv run ak makemigrations` and `make gen` have run. CI checks pending migrations (`make ci-lint-pending-migrations`) and diffs the regenerated schema/clients separately; either fails the build.
- Read the generated migration before committing — makemigrations regularly catches more than intended.
- Don't hand-write migrations unless the task is explicitly a data migration or repair. Prefer a blueprint over a data migration for managed, idempotent objects.
- **Docstrings on viewsets and serializers are public API documentation.** drf-spectacular lifts them into `schema.yml` as descriptions, from where they land in three generated clients and the API docs site. Write them for an API consumer or leave them off — a filler `"""FooViewSet"""` becomes a filler description in every client and schema-diff noise in review.

## Code conventions

- Anything user-visible is translatable: `from django.utils.translation import gettext_lazy as _`. Management command help/prompts/errors are exempt — plain English. Never edit `locale/*.po`.
- Find the existing helper before writing one: `django.utils` and the auth framework first, then `authentik/lib/` and the app you're in.
- Event contexts use `authentik.events.utils.model_to_dict` (returns app/model/pk/name only). Django's own `model_to_dict` serializes every field, secrets included.
- New `authentik.*` apps wire themselves by convention: list in `SHARED_APPS`/`TENANT_APPS`, subclass `ManagedAppConfig`, and `settings.py`/`signals.py`/`tasks.py`/`checks.py` are imported automatically. Startup reconciliation = `@ManagedAppConfig.reconcile_global` / `reconcile_tenant`, not ad-hoc `ready()` code.
- Python is pinned to 3.14 and the code uses 3.14-only syntax (PEP 758 bare multi-exception `except` appears in the tree). Don't "fix" it or write for older versions.
- mypy runs `--strict`, but an `ignore_errors` allowlist in `pyproject.toml` exempts most existing modules. New modules are outside the list and get full strict checking.

## macOS

`lxml` and `xmlsec` must compile against brew's libxml2 or SAML tests fail with linker-level errors. `make core-install` injects the right flags; a bare `uv sync` can leave broken wheels.
