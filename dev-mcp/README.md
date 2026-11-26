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

Every result says what it checked, what it skipped and what it couldn't tell, so an agent's summary
can't quietly drop the caveat.

## Setup

Claude Code reads `.mcp.json` and asks before starting the server. Codex reads `.codex/config.toml` in
trusted projects. Both run `node dev-mcp/main.ts serve` from the repo root; Node runs the
TypeScript directly. Claude Code hooks in `.claude/settings.json` lint each edited file and remind the
agent to check generated files before it stops.

## The database guard

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
`#dev-mcp/*` imports map to `dev-mcp/lib/*.ts`. Root `lint`, `format` and `build:types` cover it,
and CI runs them as the `scripts` and `check-types` lint jobs.

```shell
pnpm run test:dev-mcp         # vitest
node dev-mcp/test/smoke.ts    # start the server over stdio and call each tool
```

Hooks and `make dev-status` must keep working before `pnpm install`, because the SessionStart hook
fires on a fresh clone. Load installed packages with `await import("pkg").catch(missing)` from
`#dev-mcp/optional` rather than a top-level import, and keep `hooks.ts` to Node built-ins.
