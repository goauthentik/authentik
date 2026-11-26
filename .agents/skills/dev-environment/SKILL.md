---
name: dev-environment
description: >
    Get from a fresh authentik clone to a running stack you can log into, or get a broken
    local environment back to a known-good state. Use when someone asks to "set up authentik
    locally", or writes "I cloned the repo, how do I run it", "Postgres won't come up", "how do I
    log in the first time", "reset my dev database", or "make install fails". Day-to-day
    server runs and migrations live in backend, the web UI dev server in frontend, the docs
    site in docs, test suites in testing, lint in linting, and PRs in contributing.
---

# authentik dev environment

## Purpose

A first run needs toolchains, two dependency installs, Postgres and S3 containers,
a local config file, a migrated database and a built web UI.

This skill is the fast path and handles common setup and recovery traps.
The full reference is [Full development environment](../../../website/docs/developer-docs/setup/full-dev-environment.mdx).
For web-only work, see [Frontend development environment](../../../website/docs/developer-docs/setup/frontend-dev-environment.mdx), though a full setup is recommended for most development tasks.

## When to invoke

- "Set up my local authentik environment." / "I cloned it, now what?"
- "`make install` fails" or "esbuild didn't install."
- "How do I log in the first time?" / "I locked myself out of akadmin."
- "My dev database is broken, start me over."

Not this skill: running and restarting the server, migrations for a model change, and the `ak` shell (backend).

## Workflow

Steps are tagged: `[shell]` run a command, `[verify]` check before moving on.
Run every `make` target from the repo root.

### 1. Fresh clone to first login

1. **[shell]** Install the prerequisites listed in the developer doc: Python 3.14, `uv`,
   Rust (through rustup, with the version pinned in `rust-toolchain.toml`), Go 1.26+, Node 24+, pnpm,
   Docker with Compose v2, Make, CMake, and the native libraries (macOS:
   `brew install libxmlsec1 libpq pkg-config uv postgresql golangci-lint krb5 cmake`).
   The `postgresql`/`libpq` client tools matter: `make dev-reset` calls `dropdb` and
   `createdb` on the host.
2. **[shell]** Start the services: `docker compose -f scripts/compose.yml up -d`. This runs
   PostgreSQL 18 on `127.0.0.1:5432` (trust auth, database `authentik`) and a Zenko S3
   server on port `8020`. There's no Redis. Dramatiq uses Postgres as its broker. With
   Podman, use `podman compose`. From an agent, the `akdev_services` tool does the same. A
   native Postgres works too: create the `authentik` database and point `postgresql.*` in
   `local.env.yml` at it.
3. **[shell]** `make install`. It runs `node-install` (root pnpm install and the shared lint
   configs), `web-install`, and `core-install` (`uv sync --frozen`, which also rebuilds
   `lxml` and `xmlsec` from source on machines with Homebrew).
4. **[shell]** `make gen-dev-config`. It writes `local.env.yml` at the repo root: `debug: true`,
   Postgres user `postgres`, file storage, `web.base_url: http://localhost:9000`, and one
   worker process with one thread. Edit that file for local overrides. A second run of the
   target overwrites it (and generates a new `secret_key`).
5. **[verify]** `make dev-status` shows how this machine runs Postgres and containers,
   where each config value came from, and whether the dev MCP server's database guard
   accepts the database. If the guard flags a dev database (50 or more human users, since it
   skips the users the e2e suite tags, or a test license), it prints the `local.env.yml`
   allowlist entry to review.
6. **[shell]** `make migrate` (runs `lifecycle/migrate.py`: system migrations, then Django
   migrations).
7. **[shell]** `make web-build`. No compiled UI ships in the repo, so the pages are blank
   without it, even if you only work on the backend.
8. **[shell]** `make run` (server and worker via `uv run ak allinone`). The first boot
   applies the bootstrap blueprints and drains the initial task queue, so give it a minute.
9. **[verify]** Open http://localhost:9000 and follow the prompts to set a password for
   `akadmin`.

To skip the prompt, or to match what the Playwright e2e suite expects, export the bootstrap
credentials **before the first `make run`**. The bootstrap blueprint only applies them while
`akadmin` has no usable password:

```shell
export AUTHENTIK_BOOTSTRAP_EMAIL=test-admin@goauthentik.io
export AUTHENTIK_BOOTSTRAP_PASSWORD=test-runner
make run
```

### 2. Reset to a known-good state

Pick the smallest reset that fixes the problem.

1. **[shell]** Schema behind the code (after a pull or a branch switch): `make migrate`.
2. **[shell]** Dependencies drifted (lockfile changed): `make install`, then `make web-build`.
3. **[shell]** Database beyond repair: stop `make run` first, then `make dev-reset`. It runs
   `dev-drop-db` (drops the dev database **and** `test_<name>`), `dev-create-db`, and
   `migrate`. Everything in the instance is lost. The next `make run` recreates `akadmin`
   and the defaults, so you set the admin password again.
4. **[shell]** Containers or volumes broken: `docker compose -f scripts/compose.yml down -v`
   deletes the Postgres and S3 volumes. `up -d` creates them again. Then continue from
   `make migrate`.
5. **[verify]** `make run` comes up and you can log in.

Locked out, and want to keep the data? Mint a recovery link instead of resetting:
`uv run ak create_recovery_key 10 akadmin`, then open `http://localhost:9000/recovery/use-token/<key>/`.

## Gotchas

- **Language servers are optional, but Claude Code's LSP plugins need them on PATH.** The
  `typescript-lsp` and `rust-analyzer-lsp` plugins warn at startup without them:
  `npm install -g typescript-language-server typescript` and
  `rustup component add rust-analyzer`. `make dev-status` lists the missing ones.
- **pnpm doesn't run install scripts** unless the package is allow-listed in its workspace's
  `pnpm-workspace.yaml` (`onlyBuiltDependencies` and `allowBuilds`). If `esbuild`,
  `chromedriver` or `tree-sitter` is missing after install, see the install-scripts note in
  the developer doc, then `pnpm rebuild <package>`. Allow-listing a package is a reviewed
  change.
- **`make node-install` checks your Node and pnpm versions** (`node-preinstall`) against
  `package.json` and stops if they don't match. Switch with `nvm use 24`. The authentik-dev
  MCP server does this by itself for `akdev_install` and its checks when nvm has a version
  that fits, and `akdev_status` names the version to `nvm use` in your own shell.
- **`make dev-reset` fails with "database is being accessed by other users".** A
  `make run` that didn't fully exit still holds connections. Kill the leftover `gunicorn`
  and `dramatiq` processes, then retry.
- **The first `uv run ak ...` is slow.** `ak` hands every command to the Rust `authentik`
  binary. If none is on `PATH`, it falls back to `cargo run`, which compiles the workspace
  once.
- **Homebrew's `cargo` can shadow rustup.** If `which cargo` points at `/opt/homebrew/bin`,
  you build with Homebrew's Rust instead of the version pinned in `rust-toolchain.toml`,
  which shows up as odd compiler or clippy errors. Put rustup's toolchain first on `PATH`.
- **aws-lc-rs FIPS fails to build with GCC 14+** (Linux). Install Clang and
  `export AWS_LC_FIPS_SYS_CC=clang`.
- **macOS: Disable fork-safety in gunicorn.** Setting `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` in your shell disables fork-safety, which avoids crashes on the first DNS lookup in gunicorn workers.
