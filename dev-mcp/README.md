# authentik-dev

A local MCP server for people working on authentik's code, and the same checks as `make` targets.
It holds no credentials and only touches a local dev database.

| Tool              | Make target         | Does                                                                                             |
| ----------------- | ------------------- | ------------------------------------------------------------------------------------------------ |
| `akdev_status`    | `make dev-status`   | How this machine runs Postgres and containers, where each config value came from, the guard      |
| `akdev_generated` | `make check-gen`    | Stale migrations, `schema.yml`, `blueprints/schema.json`, locales, API clients (CI's `test-gen`) |
| `akdev_lint`      | `make lint-changed` | The CI lint jobs that cover the files changed since `origin/main`, with CI's commands            |
| `akdev_skill`     |                     | The repo's skills in `.agents/skills/`, for clients without Skills-over-MCP                      |
| `akdev_job`       |                     | The result of a long-running tool call                                                           |
| `akdev_services`  |                     | Bring the `scripts/compose.yml` containers (Postgres, S3) up or down; only with Docker or Podman |

Every result says what it checked, what it skipped and what it couldn't tell, so an agent's summary
can't quietly drop the caveat.

## Setup

Claude Code reads `.mcp.json` and asks before starting the server. Codex reads `.codex/config.toml` in
trusted projects. Both run `node dev-mcp/main.ts serve` from the repo root; Node runs the
TypeScript directly. Claude Code hooks in `.claude/settings.json` lint each edited file and remind the
agent to check generated files before it stops.

## On a fresh clone

Without `pnpm install` the server can't load the MCP SDK, so `serve` starts a setup-mode server
instead (`lib/server/fallback.ts`, Node built-ins only). Its instructions and `akdev_status` say
what's missing, and `akdev_install` runs `make install`; Claude Code asks the person before every
call. Once the dependencies are in place, from that tool or from `make install` run anywhere,
the setup server starts the real one, hands the session over and sends `tools/list_changed`, so
the full tools appear without a restart.

Both modes check the active Node against `engines.node` in `package.json`, with the same range
check `make node-preinstall` runs (`scripts/node/utils/node.ts`). When it doesn't fit and nvm
already has a version that does, `make install` and the server's checks run with that version
first on `PATH`, and `akdev_status` and the SessionStart hook give the agent the `nvm use`
command for its own shell. When no installed version fits, `akdev_install` refuses and says
which `nvm install` to run.

## The database guard

Long checks run as jobs that `akdev_job` returns. When the client sends a progress token,
`akdev_lint`, `akdev_generated` and `akdev_services` (`up`, `down`) keep the call open instead,
send a `notifications/progress` for each step, and return the finished result. The first
message names the job, so a call that times out can still be picked up. Setup mode's
`akdev_install` does the same for each `make install` prerequisite. Claude Code shows the
messages inline and the bar in the expanded view (ctrl+o).

`akdev_services` runs this machine's compose command against `scripts/compose.yml`, naming the
`postgresql` and `s3` services. `down` never passes `-v`, so the volumes and their data stay.
Claude Code asks the person before every call. Without Docker or Podman the tool isn't
registered and the guard's `running` check is skipped: a native Postgres is a supported setup.

`akdev_generated` runs Django management commands against the configured database, so it's only
registered when the guard passes. Postgres can run in Docker, Podman, natively or on a dev VM; the
guard judges the database the configuration resolves to, not the setup:

1. `debug` is true.
2. The connection is local (loopback, socket, or a container on this machine), or the host is listed.
3. The database is `authentik` or `test_authentik`, or is listed.
4. The database doesn't look like production: every installed license is a verified `dev_test`
   license, fewer than 50 human users, no logins from public addresses in the last week. A
   `dev_test` claim counts only when the license's certificate chain leads to authentik's
   licensing CA (`authentik/enterprise/public.pem`) and its signature verifies, the same checks
   as `LicenseKey.validate()`.
5. `AUTHENTIK_TOKEN` isn't set in the shell.

A dev database often trips check 4: an e2e run leaves hundreds of users. Use a `dev_test` license
for enterprise features. `make dev-status` prints the entry to add to `local.env.yml` after you've checked:

```yaml
dev_mcp:
    allowed_databases:
        - name: authentik
          ignore_signals: [users]
```

The guard stops accidents, such as a shell still pointing at production. An agent with a shell can
edit the allowlist, so changes to it are reported back in `akdev_status`.

## Development

The code is part of the root package: its dependencies are in the root `package.json`, and
`#dev-mcp/*` imports map to `dev-mcp/lib/*.ts`. `lib/` is grouped by purpose:

| Folder                                                         | Holds                                                                        |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `core/`                                                        | Git and the repo root, running commands, loading optional dependencies       |
| `results/`                                                     | The result envelope, the result store under `.git/akdev`, background jobs    |
| `environment/`                                                 | Discovery: resolved config, container runtime, where Postgres runs           |
| `guard/`                                                       | The database guard: static checks, database signals, licenses, the allowlist |
| `checks/`                                                      | `check-gen` and `lint-changed`, and the CI files they read                   |
| `agent/`                                                       | What agents read directly: Claude Code hooks and the repo's skills           |
| `server/`                                                      | The MCP server and its tools                                                 |
| Root `lint`, `format` and `build:types` cover it,              |
| and CI runs them as the `scripts` and `check-types` lint jobs. |

```shell
pnpm run test:dev-mcp         # vitest
node dev-mcp/test/smoke.ts    # start the server over stdio and call each tool
```

Hooks and `make dev-status` must keep working before `pnpm install`, because the SessionStart hook
fires on a fresh clone. Load installed packages with `await import("pkg").catch(missing)` from
`#dev-mcp/optional` rather than a top-level import, and keep `hooks.ts` to Node built-ins.
