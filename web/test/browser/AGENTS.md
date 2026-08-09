# Browser Test Conventions

These are Playwright tests run under Vitest's browser runner (Chromium). They exercise the **admin and user UIs end-to-end** against a running authentik instance. Tests live in `test/browser/*.test.ts`; supporting fixtures and helpers live in `e2e/`.

## Philosophy

**Drive the UI, not the API.** A test for a feature should exercise the same path a user takes — click "New Provider", fill the form, click "Create", verify it appears. We don't seed entities through the REST API and then click one button to verify a single side effect. If the UI flow breaks, the test must break with it; if we shortcut through the API, regressions in the wizards, modals, navigation, and form bindings go undetected.

**Cover features, not bugs.** A test file is named after the feature it exercises (`providers.test.ts`, `applications.test.ts`), not the bug it was written for. Regression tests for specific defects belong inside the feature's existing suite as an additional `test(...)` case — not as a one-off file with bespoke API plumbing.

**No bespoke HTTP clients.** If you find yourself writing a `makeAPIClient` helper inside a test, stop. Either drive the UI to create the prerequisite state, or — if the prerequisite is truly out of scope for the feature under test — extend a fixture so the pattern is reusable.

**No explicit cleanup.** Entity names are seeded with `IDGenerator.randomID(...)` so each run produces unique slugs. Stale entities from prior runs don't collide and are expected to accumulate in dev environments. Don't add `try/finally` cleanup blocks — they obscure the assertion at the end of the test and tend to swallow the real failure when the UI flow breaks.

## Imports

Tests import from the `#e2e` alias, never from `@playwright/test` directly:

```ts
import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";
```

The `#e2e` entry (`e2e/index.ts`) re-exports `expect` from Playwright and exports a `test` that has been extended with our fixtures.

## Fixtures

Destructure what you need from the test callback. All are constructed per-test:

| Fixture     | Purpose                                                                                                                                                                                                                                                                            |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `session`   | `login({ to, username?, password?, rememberMe? })`, `toLoginPage()`, `checkAuthenticated()`. Defaults to `test-admin@goauthentik.io` / `test-runner`.                                                                                                                              |
| `navigator` | `navigate(to)` and `waitForPathname(to)` — use these over `page.goto` so URL waits are consistent.                                                                                                                                                                                 |
| `form`      | `fill(label, value, ctx?)`, `search(query, ctx?)`, `selectSearchValue(label, pattern, ctx?)`, `setInputCheck(label, bool, ctx?)`, `setRadio(group, name, ctx?)`, `setFormGroup(pattern, open, ctx?)`. Knows about `ak-switch-input`, `ak-form-group`, and search-select dropdowns. |
| `pointer`   | `click(name, role?, ctx?)` — high-level click by accessible name; defaults to buttons/links.                                                                                                                                                                                       |
| `page`      | Raw Playwright `Page` for anything the fixtures don't cover. Shadow DOM is pierced automatically.                                                                                                                                                                                  |
| `baseURL`   | The instance URL, from `AK_TEST_RUNNER_PAGE_URL` (defaults to `http://localhost:9000`).                                                                                                                                                                                            |

Most steps in most tests should go through `form` and `pointer`. Reach for `page.locator(...)` only when there isn't a fixture method that fits.

## Shape of a test

```ts
test.describe("Feature name", () => {
    const names = new Map<string, string>();

    test.beforeEach("Seed names", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        names.set(testId, `${randomName(seed)} (${seed})`);
    });

    test("Do the thing", async ({ session, navigator, form, pointer, page }, testInfo) => {
        const name = names.get(testInfo.testId)!;
        const { fill, search, selectSearchValue } = form;
        const { click } = pointer;

        await test.step("Authenticate", async () => {
            await session.login({ to: "/if/admin/#/core/providers" });
        });

        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Open wizard", async () => {
            await expect(dialog, "Wizard is initially closed").toBeHidden();
            await click("New Provider");
            await expect(dialog, "Wizard opens").toBeVisible();
        });

        await test.step("Fill form", async () => {
            await series(
                [click, "OAuth2/OpenID", "option"],
                [fill, "Provider Name", name],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create"],
            );
        });

        await test.step("Verify created", async () => {
            await expect(await search(name), "Provider is visible").toBeVisible();
        });
    });
});
```

Conventions baked in above:

- **`test.describe` per feature**, plain imperative names per test.
- **`test.step(...)` for every meaningful phase** — these show up in traces and HTML reports and make failures self-locating.
- **Names keyed by `testId`** in a module-scoped `Map`, populated in `beforeEach`.
- **`series([fn, ...args], ...)`** for ordered form-fill sequences. Reads top-to-bottom as a script of user actions.
- **Dialog locator captured once**, then passed as the `ctx?` argument to scope `fill`/`click`/`selectSearchValue` inside it.
- **Every `expect` has a message** as the second argument — it shows up in the failure output. Phrase it as the property being asserted ("Wizard opens", "Provider is visible"), not as a restatement of the matcher.
- **First parameter must be a destructure pattern**, even when you don't reference any fixture — write `async ({ page: _page }, { testId }) => {…}`. A bare identifier (`async (_, { testId }) => {…}`) throws `First argument must use the object destructuring pattern` at runtime because Playwright inspects the parameter pattern to decide which fixtures to inject, and an empty destructure (`async ({}, { testId }) => {…}`) trips ESLint's `no-empty-pattern`. Destructure-and-rename is the only form that satisfies both.

## Locator preferences

In order, prefer:

1. **ARIA role queries** — `page.getByRole("button", { name: "Create" })`, `page.getByRole("dialog", { name: /Launch Endpoint/i })`, `page.getByLabel("Username")`. These survive style/markup changes and document intent.
2. **Web component tags** — `page.locator("ak-stage-identification")`, `page.locator("ak-form-group", { hasText: /Advanced/ })`. Stable element contracts.
3. **`data-test-id`** — `page.getByTestId("...")`. The Playwright config sets `testIdAttribute: "data-test-id"`. Only add a new test id when role/label queries can't disambiguate.
4. **CSS selectors** — last resort.

Shadow DOM works transparently — don't write `.shadowRoot` traversals; Playwright pierces.

## Assertions

```ts
await expect(dialog, "Dialog is initially closed").toBeHidden();
await expect(dialog, "Dialog opens").toBeVisible();
await expect(row, "Endpoint row appears without manual refresh").toBeVisible({ timeout: 5_000 });
await expect(input, "Input has expected value").toHaveValue("foo");
await expect(checkbox, "Checkbox is checked").toBeChecked();
```

- Always pass a message.
- Use explicit `{ timeout: ... }` only when the default (5s) genuinely isn't enough — generally for the first assertion after an async UI transition like a dialog mount or a navigation.
- Don't add `page.waitForTimeout` — wait for the locator condition you actually care about.

## Anti-patterns (do not do these)

- **Bespoke API clients in test files.** No `makeAPIClient`, no raw `fetch(`${baseURL}/api/v3/...`)` for setup. See [Philosophy](#philosophy).
- **Reading `process.env.AK_TEST_BOOTSTRAP_TOKEN`** from a test. Tests authenticate as a real user via `session.login()`.
- **One-file regression tests for a single bug.** Add a `test(...)` case to the relevant feature suite instead.
- **`try/finally` cleanup blocks.** Names are randomized; let entities accumulate.
- **`page.goto` with no wait.** Use `navigator.navigate(to)` or `session.login({ to })`.
- **Asserting against CSS selectors when a role/label exists.** If you find yourself writing `.locator('button[type="submit"]')`, check whether `getByRole("button", { name: ... })` works first.
- **Skipping `test.step`.** Long flat tests are hard to debug; wrap each phase.

## Adding new coverage

When extending an existing suite, follow the surrounding patterns — same fixture destructure, same `Map<testId, name>` style, same dialog-as-context idiom. When introducing a new suite, model the structure on `applications.test.ts` or `providers.test.ts`; those are the canonical examples.

If you need a helper that doesn't exist yet (a new form input shape, a new common navigation), extend the fixture in `e2e/fixtures/` rather than duplicating logic in tests.

## Running

```bash
npm test                                # All Vitest (unit + browser)
npx vitest run test/browser/foo.test.ts # Single browser test file
```

The Playwright config (`playwright.config.js`) is also present for the `npm run test:e2e` path and configures Chromium with traces on first retry and a dark color scheme. The browser tests through Vitest use `@vitest/browser-playwright` and target the same `test/browser/` directory.
