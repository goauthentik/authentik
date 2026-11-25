---
name: testing
description: >
    Run the authentik tests that touch your change, run one e2e test in a visible browser,
    chase a flaky test, and work out why a suite won't start or hangs. Covers Python/Django
    (`make test <path>`), Go, Rust, the web Vitest tests, the Playwright suite under
    web/test/browser, and the Selenium e2e suite under tests/e2e. Use when someone says
    "run just my tests", "run one test", "watch the e2e test in a browser", "this test is
    flaky", "the tests hang", or "the e2e suite won't start". Lint and type checks belong to
    linting; installing tools and resetting the database to dev-environment; running the
    server to backend.
---

# authentik testing

## Purpose

authentik has five test runners. Running all of them takes far too long to do on every
change, so the fast path is to run only the ones near your change and leave the rest to CI.
This skill gives the narrow command for each, plus the traps that make a suite hang, time
out, or fail for reasons unrelated to your change.

**What to test.** Tests follow customer paths through the product: a user logs in, enrolls
MFA, finishes a flow, an admin creates a provider. A fix earns coverage when such a path
would have caught it. Don't add a narrow test that restates the bug you just fixed; that's
scar tissue, not coverage. Prefer extending an existing flow-level or e2e path.

Conventions for web tests are in `web/test/AGENTS.md` and `web/test/browser/AGENTS.md`.
E2E setup is in `website/docs/developer-docs/setup/full-dev-environment.mdx`
("End-to-end (E2E) setup").

## Workflow

Steps are tagged: `[shell]` run a command, `[verify]` check before moving on. Run from the
repo root.

### 1. Run only what touches your change

- **[shell] Python, by path:** `make test authentik/providers/saml` (any file or directory).
  It runs `coverage run manage.py test --keepdb <path>` through the pytest runner.
- **[shell] Python, one test:** `make` can't take `::`, so call the runner directly:
  `uv run manage.py test --keepdb authentik/core/tests/test_models.py::TestModels::<test_name>`.
  Dotted labels (`authentik.core.tests.test_models.TestModels`) also work.
- **[shell] Go:** `go test -run TestName ./internal/outpost/ldap/...` (all: `make go-test`).
- **[shell] Rust:** `cargo nextest run <filter>` (all: `make rust-test`).
- **[shell] Web unit tests:** `pnpm --dir web exec vitest run --project "Unit Tests" <file>`
  (what CI runs). `make web-test` starts Vitest in watch mode; `make web-test-unit` runs once.
- **[verify]** The run reports the test count you expect. A label that resolves to nothing
  logs `Test file not found` and exits 1.

### 2. One e2e test in a visible browser

**Selenium (`tests/e2e/`).** Tests drive a remote Chrome at `localhost:4444`.

1. **[shell]** `COMPOSE_PROFILES=selenium docker compose -f tests/e2e/compose.yml up -d`.
   The Chrome service is behind the `selenium` profile; without it only mailpit starts.
2. **[shell]** Build the UI the live server will serve: `make web-build` and
   `pnpm --dir web run build:sfe` (CI does both).
3. **[shell]** `make test tests/e2e/test_flows_login.py`, or one method with `::` as above.
4. **[verify]** Watch at `http://localhost:7900` (noVNC, password `secret`), or VNC on 5900.

**Playwright (`web/test/browser/`).** Runs against a live instance at `localhost:9000`
(override with `AK_TEST_RUNNER_PAGE_URL`), logging in as `test-admin@goauthentik.io` /
`test-runner` (seeded by `web/test/blueprints/test-admin-user.yaml`; see the dev docs for
the bootstrap env vars).

1. **[shell]** Once: `pnpm --dir web exec playwright install --with-deps chromium`.
2. **[shell]** `make run`, then in `web/`:
   `pnpm exec playwright test test/browser/300-users.test.ts --headed --workers=1`
   (`--ui` or `--debug` to step through).
3. **[verify]** After a failure: `pnpm --dir web exec playwright show-report`.

Colocated component tests (`*.browser.test.ts`) run in Vitest's "Browser Tests" project,
which is configured headless.

### 3. Debug a flaky test

1. **[shell] Python order dependence:** tests run in random order (pytest-randomly). Rerun
   with the seed from the failing log: `--randomly-seed=<n>` (CI sets `CI_TEST_SEED`; the
   runner reads it as the default).
2. **[shell] Python repeat:** `--count 20` reruns the selection (pytest-flakefinder).
   `--no-capture` shows prints.
3. **[shell] Playwright load:** rerun the failing file alone with
   `--workers=1 --max-failures=0`, and `--repeat-each=10` to reproduce. Read the failure
   screenshot before blaming your change.
4. **[verify]** Selenium tests retry only in CI (`RETRIES`, default 3); locally a test runs
   once, so a flake shows up locally that CI hides.

### 4. A suite won't start, or hangs

- **Python tests hang with dramatiq "connection is closed ... retried in 5 seconds".** Not a
  test failure: a background task hit a column your dev DB lacks. Scroll up for the
  `ProgrammingError`, then `make migrate`. If a rebased migration was renamed and migrate
  says `column ... already exists`, fix the row in `django_migrations` or `make dev-reset`
  (it also drops the `test_` database).
- **Selenium: `Webdriver failed after 1`.** Chrome isn't up on 4444: missing
  `COMPOSE_PROFILES=selenium`, or Docker Desktop without host networking (Settings >
  Resources > Network > Enable host networking; the service uses `network_mode: host`).
- **Playwright fails in `prerequisites.setup.ts`.** No server at the base URL, or default
  blueprints not applied yet. It polls for 90 s, then fails.
- **Rust tests or server won't compile on a fresh clone:** `include_str!` needs
  `web/dist/standalone/loading/startup.html`; run `make web-build` once.
- **Rust test binary aborts with a `Python3.framework` dyld error (macOS):** set
  `PYO3_PYTHON` to the project's Python before building.

## Gotchas

- **Parallel Playwright runs time out under load.** Default is 50% workers against one dev
  server; wizards sit on skeletons and tables never render. Confirm with `--workers=1`.
- **Stale selectors fail as 30 s timeouts, not "not found".** Use the fixtures
  (`session.login()`, `session.signOut()`; sign-out sits behind the "Switch user" menu)
  instead of re-deriving locators.
- **Leftover test data breaks stock defaults.** Pickers load one page, so dozens of extra
  flows can push `default-*` entries off it. Never seed flows with the `authentication`
  designation and a slug sorting before `default-`: with no brand flow set, the executor
  picks the first by slug and every login breaks.
- **`@vendor-network` CAPTCHA tests** need the vendors' servers; CI skips them.
- **Colocated `src/**/*.test.ts` files aren't type-checked** by `tsc`; type errors in
  them pass CI. Test Lit components through their public surface, not protected members.
