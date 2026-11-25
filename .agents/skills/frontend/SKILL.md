---
name: frontend
description: >
    Run the authentik web UI against your local backend with live reload, build the
    production bundle, and find out why a UI edit isn't showing up. Use when someone says
    "start the web UI in watch mode", "rebuild the frontend", "my change doesn't appear in
    the browser", "the admin page is still the old version", or "build web/dist". First-time
    setup belongs to dev-environment, the Django server to backend, lint and type checks to
    linting, the web tests to testing, and the docs site to docs.
---

# authentik web UI development

## Purpose

The web UI (`web/`) is three Lit apps (Admin, User, Flow) bundled by esbuild into
`web/dist/`. The server doesn't proxy a dev server: it serves whatever files are in
`web/dist/` at the moment of the request. So "running the frontend" means keeping
`web/dist/` up to date while `make run` serves it. Most "my edit doesn't show" problems come
from that.

Architecture, conventions, i18n and the API client rules are in
[`web/AGENTS.md`](../../../web/AGENTS.md). Read it before changing components. The repo uses
**pnpm**; use the `make` targets or `pnpm --dir web ...` from the root.

Setup docs: `website/docs/developer-docs/setup/frontend-dev-environment.mdx` (UI only,
against a container backend) and `full-dev-environment.mdx` (everything local).

## When to invoke

- "Start the web UI with hot reload."
- "Build the production bundle."
- "I changed a component and the browser still shows the old one."
- "The flow page for old browsers didn't change."

Not this skill: installing Node, pnpm and dependencies (dev-environment), running the
backend (backend), web tests (testing), lint and `tsc` (linting).

## Workflow

Steps are tagged: `[shell]` run a command, `[verify]` check before moving on. Commands run
from the repo root.

### 1. Run the UI with live reload

1. **[shell]** Dependencies, once and after lockfile changes: `make node-install web-install`.
   `node-install` runs `scripts/node/lint-runtime.ts` first and stops if your Node or pnpm
   version doesn't match `package.json` (`engines` and `packageManager`).
2. **[shell]** Backend in one terminal: `make run` (serves `http://localhost:9000`).
3. **[shell]** Watcher in another: `make web-watch`. It runs `build-locales` once, then
   `node scripts/build-web.ts --watch`, which rebuilds `web/dist/` on save and adds a
   live-reload plugin.
4. **[verify]** Edit a component, wait for the watcher to log a rebuild, and check the page
   at `http://localhost:9000` reloads with the change.

### 2. Build the production bundle

- **[shell]** `make web-build` (`pnpm --dir web run build`, wireit-orchestrated, writes
  `web/dist/`).
- **[shell]** The simplified flow executor for old browsers is a separate package and is not
  part of `build` or `watch`: `pnpm --dir web run build:sfe`. CI builds both before the
  Selenium e2e jobs.
- **[verify]** `web/dist/` has fresh timestamps and the UI loads under `make run`.

### 3. "My edit doesn't show up"

Work down this list. Each step rules out one layer.

1. **[verify] Is the watcher running and did it rebuild?** A syntax or import error stops
   the rebuild and the old bundle stays in `web/dist/`. Read the watcher output.
2. **[verify] Are you editing what gets bundled?** Locale changes only compile at watcher
   start (`build-locales`); restart `make web-watch` after editing `xliff/` or locale
   config. SFE changes need `build:sfe` (above).
3. **[verify] Is the server serving this checkout's `web/dist/`?** The Rust server
   (`src/server/static.rs`) serves `./web/dist/` relative to its working directory under
   `/static/dist/` and `/if/{admin,user,flow/<slug>,rac/<slug>}/assets/`. Start `make run`
   from the repo root of the same worktree you are editing. A second worktree or a
   container backend serves its own `dist`.
4. **[verify] Is the browser cache in the way?** Static responses carry
   `Cache-Control: public, no-transform` with no `max-age`, so the browser may reuse an
   old file. Hard-reload, or tick **Disable cache** in DevTools > Network while working.
5. **[verify] Is it compiled into the server binary?** `web/dist/standalone/loading/startup.html`,
   `web/robots.txt` and `web/security.txt` are embedded with `include_str!`. Changing them
   needs a Rust rebuild (restart `make run`), not just a web rebuild.
6. **[verify] Is it an API change?** New serializer fields reach the UI only after
   `make gen` regenerates `packages/client-ts` (`@goauthentik/api`). The client resolves to
   its TypeScript source, so no separate client build is needed after regenerating.

## Gotchas

- **The dev server is Rust, not Go.** `ak server` / `ak allinone` run the Rust binary;
  `cmd/server/` and `internal/web/` are no longer launched. Look in `src/server/` for
  static-serving behavior.
- **A fresh clone needs `web/dist/` before the Rust server compiles**, because of the
  `include_str!` files above. Run `make web-build` once. (CI's Rust job writes placeholder
  files instead.)
- **`make web-build` runs `node-install`, not `web-install`.** After a `web/pnpm-lock.yaml`
  change, run `make web-install` too or the build uses stale packages.
- **Don't point `@goauthentik/api` back at `dist/`.** `packages/client-ts/package.json`
  points `main`/`types` at `src/index.ts` on purpose; every consumer is a bundler.
- **Storybook** for visual work: `make web-storybook-watch` (port 6006).
