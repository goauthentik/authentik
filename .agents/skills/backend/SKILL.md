---
name: backend
description: >
    Run authentik's Django backend while you work on it and take a model change to a
    committed migration. Use when someone asks to "run the server", "restart on save",
    "start the worker", "my tasks aren't running", "I changed a model, make the migration",
    "CI reports missing migrations", "open a Django shell", or "run an ak command".
    First-time setup and resets live in dev-environment. The web UI is in frontend, test
    suites in testing, lint and mypy in linting, docs in docs, and PRs in contributing.
---

# authentik backend development

## Purpose

The backend is a Django app served by gunicorn behind a Rust front server,
plus a Dramatiq worker that uses Postgres as its broker.

Day to day you run both, change code, and keep models, migrations and the generated API schema in sync.
CI fails a PR on any of the three drifting. Setup is in the [full development environment](../../../website/docs/developer-docs/setup/full-dev-environment.mdx) doc.
Debugger setup is in [debugging](../../../website/docs/developer-docs/setup/debugging.mdx).

## When to invoke

- "Run the backend" / "auto-restart when I save."
- "I changed `models.py`, what now?" / "`ci-lint-pending-migrations` failed."
- "Open a Django shell" / "run a management command."
- "Tests or the worker hang with 'connection is closed'."

Not this skill: a fresh clone or a reset database (dev-environment).

## How `ak` works

`ak` is the console script from `lifecycle/ak.py`. `allinone`, `server`, `worker`,
`healthcheck`, `test-all` and a few others go to the Rust `authentik` binary (built from
`src/`). `ak` falls back to `cargo run --` when no binary is on `PATH`. Anything else becomes
`authentik manage -- <args>`, which runs `python -m manage <args>`. So
`uv run ak makemigrations` is plain Django `manage.py makemigrations`. The old Go server in
`cmd/server/` and `internal/web/` is no longer launched by any command. Server-side changes
there have no effect at runtime. Go is only the outposts.

## Workflow

Steps are tagged: `[shell]` run a command, `[edit]` change code, `[verify]` check before
moving on. Run from the repo root.

### 1. Run the server and worker

1. **[shell]** `make run` runs `uv run ak allinone`: server and worker in one process tree,
   at http://localhost:9000.
2. **[shell]** For restart-on-save, install [watchexec](https://github.com/watchexec/watchexec)
   and run `make run-watch`. It restarts everything on `.py` and `.rs` changes only. Web UI
   changes need `make web-watch` (frontend skill).
3. **[shell]** Separate processes, if you only need one: `uv run ak server`,
   `uv run ak worker`.
4. **[verify]** `curl -i http://localhost:9000/-/health/ready/` returns 200.

### 2. Model change to committed migration

1. **[edit]** Change `authentik/<app>/models.py`.
2. **[shell]** `uv run ak makemigrations <app_label>` (or `make make-migrations` for all
   apps). The command is overridden in `authentik/commands/` with a pgtrigger-aware
   autodetector, so always use it rather than a stock Django one.
3. **[verify]** Read the new `authentik/<app>/migrations/NNNN_*.py`. Give it a descriptive
   name (`--name`), check that renames weren't generated as drop + add, and that the file
   holds only your app's changes, with no fields from someone else's unmigrated model.
4. **[shell]** `make migrate`.
5. **[shell]** `make test authentik/<app>` (runs with `--keepdb`).
6. **[shell]** If a serializer, viewset or model field the API exposes changed: `make gen`.
   It rebuilds `schema.yml` and `blueprints/schema.json` and the Go, Rust and TS clients.
   Commit `schema.yml` and `blueprints/schema.json`. Never hand-edit either.
7. **[verify]** `make check-gen` passes with every generated file current. It checks missing
   migrations, `schema.yml`, `blueprints/schema.json`, locales, and API clients that probably
   need regenerating. It runs the same checks as CI's `test-gen` and `pending-migrations` jobs
   and writes no files. From an agent, the `akdev_generated` tool does the same.
   `make ci-lint-pending-migrations` (`makemigrations --check`) is the single CI check.
   `make ci-lint-migrations` lints the migrations added since `origin/main` (override with
   `MIGRATIONS_BASE=`).
8. Commit the model change and its migration together.

### 3. Django shell and management commands

- **[shell]** `uv run ak shell` opens a Django shell with all models imported. Objects you
  save there are logged as events by the `authentik-shell` user.
- **[shell]** Non-interactive: `uv run ak shell -c "..."` for one-liners, or
  `uv run ak shell < script.py` for anything longer.
- **[shell]** `uv run ak dbshell` opens `psql` on the dev database.
- **[shell]** Useful authentik commands: `create_recovery_key <minutes> <user>`,
  `apply_blueprint <path>`, `export_blueprint`, `changepassword`, `repair_permissions`,
  `build_schema`. `uv run ak help` lists them all.
- **[shell]** `uv run ak dump_config [keys]` prints the merged config (defaults,
  `local.env.yml` and `AUTHENTIK_*` env vars).

## Gotchas

- **Tests or the worker hang, printing "connection is closed ... will be retried in 5
  seconds".** Not Redis (there's none) and not a test failure. Scroll up: a task hit a
  column the dev database doesn't have yet (`ProgrammingError: column ... does not exist`),
  which poisoned the connection, and Dramatiq retries forever. Run `make migrate`.
- **After a rebase, `make migrate` fails with `column "<x>" already exists`.** Your branch's
  migration was renumbered, and the dev DB still records the old name. Rename the record
  instead of dropping the column, in `uv run ak dbshell`:
  `update django_migrations set name='<new>' where app='<app>' and name='<old>';`
- **A migration you rewrote after applying it never runs again.** Django tracks migrations
  by name, so `make migrate` is a no-op and the API 500s on the missing column. Roll back to
  the previous migration (`uv run ak migrate <app> <previous>`) before editing an applied
  migration, or reset the database (dev-environment).
- **Two branches added the same migration number.** Rerun `uv run ak makemigrations --merge`,
  or renumber yours and fix its `dependencies`.
- **Rust changes need a rebuild.** `make run-watch` restarts on `.rs` saves. Under plain
  `make run`, restart it. On macOS, Rust tests run with `cargo` may abort at launch with
  `Library not loaded: @rpath/Python3.framework/Versions/3.9`. Set `PYO3_PYTHON` to the
  project's Python 3.14 interpreter.
- **Homebrew's `cargo` shadows rustup** if `/opt/homebrew/bin` comes first on `PATH`, so
  you build with a different Rust than `rust-toolchain.toml` pins. Clippy then reports
  phantom "lint expectation is unfulfilled" errors. Check `cargo --version`.
