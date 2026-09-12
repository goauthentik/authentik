# Unit Test Conventions

Pure-Node, no-browser tests for individual functions, pure logic, and modules with no DOM dependencies. Runs under Vitest's Node environment — no Playwright, no Lit rendering, no live authentik instance.

## When a unit test is the right tool

- The thing under test is a **plain function or class** with no DOM, network, or component lifecycle.
- You want to cover **branches, edge cases, error paths, and invariants** thoroughly and fast.
- The behavior is deterministic given inputs — no timers, no external services, no `customElements.define`.

If the answer involves rendering a Lit component, clicking something, awaiting network, or asserting against the DOM, it does not belong here. Push it to a colocated Lit component test or to `test/browser/`.

## File layout

- Files live in `test/unit/*.test.ts`.
- One file per module/feature under test — name it after the symbol or module (`lexer.test.ts`, `authenticator-validate-challenge-selection.test.ts`).
- The Vitest config also picks up `**/*.unit.test.ts` anywhere in the workspace, so a tightly-coupled test may be colocated next to its source as `foo.unit.test.ts` when that's clearer than a parallel `test/unit/` file.

## Imports

```ts
import { describe, expect, it, vi } from "vitest";

import { shouldResetSelectedChallenge } from "#flow/stages/authenticator_validate/challenge-selection";
```

- Use `describe` / `it` / `expect` from `vitest`. Do **not** import `test`/`expect` from `#e2e` — that's for browser tests and pulls in Playwright.
- Reach into source via the package `#alias` imports (`#flow/…`, `#elements/…`, `#common/…`) — never relative paths into `src/`.
- Use `vi` for spies, mocks, and timers. Prefer real implementations; only mock at module boundaries that actually pose a problem (network, time, randomness).

## Shape of a test

```ts
describe("shouldResetSelectedChallenge", () => {
    it("returns true when the previously selected challenge is no longer allowed", () => {
        const selected = makeDeviceChallenge(DeviceClassesEnum.Email, "email-1");
        const allowed = [
            makeDeviceChallenge(DeviceClassesEnum.Totp, "totp-1"),
            makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1"),
        ];

        expect(shouldResetSelectedChallenge(selected, allowed)).toBe(true);
    });

    it("returns false when the previously selected challenge is still allowed", () => { ... });
    it("returns false when there was no selected challenge", () => { ... });
});
```

Conventions:

- **`describe(symbolName)`** at the top, optionally nested by method or behavior (`describe("addRule")`, `describe("tokenization")`, `describe("states")` — see `lexer.test.ts`).
- **`it("returns X when Y")`** — full sentences starting with the verb. State both the outcome and the precondition. Bad: `"works"`, `"handles nulls"`. Good: `"returns null once the input is exhausted"`, `"rolls back the lexer index when an action rejects"`.
- **Arrange / act / assert** with a blank line between phases where it improves scanability. Inline factories like `makeDeviceChallenge(...)` for repeated test-data shapes — keep them at the top of the file, not in shared helpers, until two files need the same one.
- **One concept per `it`.** If you reach for "and" in the name, split it.
- **No assertion messages** on `expect()` in unit tests. The test name and matcher already describe intent; Vitest's output is sufficient.

## Assertions

Plain Vitest matchers — `toBe`, `toEqual`, `toBeNull`, `toBeTruthy`, `toThrow(/regex/)`, `toHaveBeenCalledTimes`, etc. Use:

- `toBe` for primitives and reference identity.
- `toEqual` for structural equality.
- `toThrow(/regex/)` for error paths — match a stable fragment of the message, not the whole thing.
- `.mock.calls[i]?.[j]` to assert on spy arguments precisely.

## Mocking and spies

```ts
const defunct = vi.fn((chr: string) => `?${chr}`);
expect(defunct).toHaveBeenCalledTimes(2);
expect(defunct.mock.calls[0]?.[0]).toBe("@");
```

- Prefer constructing test doubles inline with `vi.fn()` over module-level `vi.mock(...)`.
- Reach for `vi.useFakeTimers()` only when the code under test reads the clock — don't preemptively fake time.
- If you need `vi.mock("module")`, hoist it to the top of the file and explain _why_ in a one-line comment if the reason isn't obvious from the import.

## What NOT to do here

- **Do not import from `@playwright/test` or `#e2e`.** Those are for browser tests.
- **Do not call `customElements.define` or import Lit components.** The Node environment has no DOM. Component coverage belongs in `test/browser/` (or a `.browser.test.ts` colocated with the component, once the Lit render helper has a real consumer).
- **Do not hit the network or filesystem.** Pure-function tests; if the unit needs IO, you're testing the wrong layer.
- **Do not silently pass on `try/catch`.** Use `expect(() => …).toThrow(...)` for error paths so a missing throw fails the test.
- **Do not assert against snapshots** unless the output is a stable, intentional artifact (e.g. a token stream). Snapshots rot fast when used as a substitute for thinking about the contract.

## Running

```bash
npx vitest run test/unit                            # All unit tests
npx vitest run test/unit/lexer.test.ts              # One file
npx vitest test/unit/lexer.test.ts -t "tokenization" # Filter by name
```

The `npm test` script runs both the unit and browser projects; for fast iteration on a pure-logic change, run the single file directly.
