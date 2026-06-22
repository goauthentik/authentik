# Test Directory Router

This directory holds three flavors of automated tests for the authentik WebUI. Each has its own conventions doc — **read the relevant one before writing or modifying tests there.**

| Directory          | What lives here                                                                                                           | Runner / environment                                    | Conventions                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| `test/unit/`       | Pure-Node tests for functions, classes, and modules with no DOM dependency.                                               | Vitest, Node environment.                               | [`test/unit/AGENTS.md`](unit/AGENTS.md)       |
| `test/browser/`    | End-to-end tests that drive the admin and user UIs in Chromium against a running authentik instance.                      | Vitest browser provider (Playwright) + `#e2e` fixtures. | [`test/browser/AGENTS.md`](browser/AGENTS.md) |
| `test/lit/`        | Shared Lit render helpers (`renderLit`, `LitViteContext`) for component-level browser tests. No tests live here directly. | —                                                       | —                                             |
| `test/blueprints/` | YAML blueprints (e.g. `test-admin-user.yaml`) seeded into authentik for browser tests to authenticate against.            | —                                                       | —                                             |

## Picking the right flavor

Walk this list top-to-bottom and stop at the first match:

1. **Pure function, no DOM, no network?** → `test/unit/`. Cheap, fast, branch-heavy coverage. See [`unit/AGENTS.md`](unit/AGENTS.md).
2. **A feature flow the user actually clicks through** (wizard, dialog, navigation, list table, login)? → `test/browser/`. Drive the real UI; do not write a unit test with a `@goauthentik/api` client to fake it. See [`browser/AGENTS.md`](browser/AGENTS.md).
3. **Regression for a specific bug?** Find the feature suite in `test/browser/` it belongs to and add another `test(...)` there. Do **not** create a new file scoped to the bug. If the bug is in a pure function, add an `it(...)` to the matching `test/unit/` file instead.
4. **Lit component behavior in isolation** (a component's lifecycle, slots, events, reactive updates, with no whole-app context)? Colocate as `Component.browser.test.ts` next to the source — the Vitest config picks up `**/*.browser.test.ts`, and `test/lit/setup.js` exposes `page.renderLit(...)` for mounting. No consumers exist yet, so check with the team before adding the first one.

If you're tempted to do something that doesn't fit cleanly into one bucket — a unit test that imports a Lit component, a browser test that calls the REST API to seed data — that's a strong signal you've chosen the wrong bucket. Re-read the conventions doc for the bucket you actually want.

## Cross-cutting rules

These apply everywhere in `test/`:

- **No bespoke API clients.** Never build a `fetch`-based admin client inside a test file. Unit tests don't need one; browser tests must drive the UI; if a real seeding gap exists, extend a fixture or blueprint instead.
- **No hard-coded credentials beyond what's already in fixtures.** Browser tests authenticate via `session.login()` using the bootstrap admin from `test/blueprints/test-admin-user.yaml`. Don't read `process.env.AK_TEST_BOOTSTRAP_TOKEN` from a test.
- **Deterministic naming for entities.** When a browser test creates data, use `IDGenerator.randomID(...)` for uniqueness — see browser conventions. Unit tests should never need this.
- **One file per feature / symbol.** Resist creating one-off files named after a bug, a ticket, or a date.
- **Test names are full sentences.** `"returns null once the input is exhausted"`, `"Create application with existing provider"`. Not `"works"`, not `"#22383"`.

## Running

```bash
npm test                                 # Both projects (unit + browser)
npx vitest run test/unit                 # Just unit tests
npx vitest run test/browser              # Just browser tests
npx vitest run path/to/single.test.ts    # One file
npm run test:e2e                         # Playwright e2e CLI path (same test/browser sources)
```

Browser tests require a running authentik instance reachable at `AK_TEST_RUNNER_PAGE_URL` (defaults to `http://localhost:9000`). The `prerequisites.setup.ts` health check will fail loudly if it isn't up.

## Where things live

- Playwright fixtures (`session`, `navigator`, `form`, `pointer`) and the `#e2e` entry point: `e2e/`.
- Lit render helper for component tests: `test/lit/`.
- Seed blueprints (test admin user, etc.): `test/blueprints/`.
- Generators (`IDGenerator`, `randomName`) used by browser tests: `e2e/utils/generators.ts` and `@goauthentik/core/id`.
