# ak-search-select Anchored Popover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `ak-search-select`'s `ak-portal`/floating-ui dropdown with an anchored native popover so the option list escapes modal `<dialog>` clipping and positions itself smartly, using no external positioning library.

**Architecture:** `ak-search-select-view` renders `ak-list-select` as a `popover="auto"` element in its own shadow DOM (no DOM relocation). The Popover API puts the menu in the browser top layer (escapes the dialog's `overflow: hidden` and stacks above it); CSS anchor positioning (`anchor-name` / `position-anchor` / `anchor()` / `anchor-size()` / `position-try-fallbacks`) handles placement, width-matching, and flip-on-overflow. `ak-portal.ts` and the `@floating-ui/dom` dependency are deleted.

**Tech Stack:** TypeScript, Lit 3, PatternFly 4, native Popover API + CSS Anchor Positioning, Vitest browser mode (Playwright/Chromium), Playwright e2e.

## Global Constraints

- Product name is always lowercase `authentik`, including comments and commit messages.
- No external positioning library — native Popover API + CSS anchor positioning only. Do **not** reintroduce `@floating-ui/dom`.
- Web UI must call the API only through `@goauthentik/api` (not relevant to this change, but no `fetch`/Axios).
- Custom-element prefix `ak-`; `elements/` must not depend on app context.
- Prefer import aliases (`#elements/*`) over deep relative paths.
- Do not add a Claude co-author trailer to commits.
- `tsconfig.json` uses `"useDefineForClassFields": false` — do not change it.
- No Firefox positioning fallback in this change (revisit later only if needed).

---

## File Structure

- **Modify** `web/src/elements/forms/SearchSelect/ak-search-select-view.ts` — remove portal usage + `inputRefIsAvailable` gate; add anchor-name/popover markup, positioning styles, `showPopover`/`hidePopover` wiring, `toggle`-sync, and the reopen guard.
- **Delete** `web/src/elements/forms/SearchSelect/ak-portal.ts` — the entire element.
- **Modify** `web/package.json` — remove the `@floating-ui/dom` dependency (its only consumer is being deleted).
- **Modify** `web/e2e/fixtures/FormFixture.ts` — repoint `selectSearchValue` from the portal's `data-managed-for` container to the in-place `ak-list-select` popover.
- **Create** `web/src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts` — colocated Vitest browser test proving top-layer escape from a `<dialog>`, width-match, and open/close sync.

> **Note on the colocated browser test:** `test/AGENTS.md` says colocated `*.browser.test.ts` for component-in-isolation behavior has "no consumers yet, check with the team before adding the first one." This plan adds the first one deliberately — it is the only way to assert the top-layer-escape behavior in isolation, and the plan was approved with this in mind. The existing `test/browser/600-providers.test.ts` suite remains the integration safety net (Task 3).

---

## Reference: current code being replaced

`ak-search-select-view.ts` today (relevant excerpts):

```ts
// line 2
import "#elements/forms/SearchSelect/ak-portal";

// lines 222-223
@state()
protected inputRefIsAvailable = false;

// lines 245-256
public override updated() {
    this.setAttribute("data-ouia-component-safe", "true");
}

public override firstUpdated(changed: PropertyValues<this>) {
    super.firstUpdated(changed);
    // Route around Lit's scheduling algorithm complaining about re-renders
    requestAnimationFrame(() => {
        this.inputRefIsAvailable = Boolean(this.#inputRef?.value);
    });
}

// lines 510-532 (menu render)
${this.inputRefIsAvailable
    ? html`
          <ak-portal name=${ifDefined(this.name)} .anchor=${this.#inputRef.value} ?open=${open}>
              <ak-list-select
                  id="menu-${this.getAttribute("data-ouia-component-id")}"
                  ${ref(this.#menuRef)}
                  .options=${this.managedOptions}
                  value=${ifDefined(this.value)}
                  @change=${this.#changeListener}
                  @blur=${this.#blurListener}
                  emptyOption=${ifPresent(emptyOption)}
                  actionLabel=${ifPresent(this.actionLabel)}
                  @ak-select-action=${this.#actionListener}
                  @keydown=${this.#listKeydownListener}
                  @keyup=${this.#listKeyupListener}
              ></ak-list-select>
          </ak-portal>
      `
    : nothing}
```

The `#clickListener` (lines 276-281) toggles `this.open`:

```ts
#clickListener = (_ev: Event) => {
    if (this.readOnly) return;
    this.open = !this.open;
    this.#inputRef.value?.focus();
};
```

---

### Task 1: Anchored popover in `ak-search-select-view` (delete portal + floating-ui)

**Files:**
- Modify: `web/src/elements/forms/SearchSelect/ak-search-select-view.ts`
- Delete: `web/src/elements/forms/SearchSelect/ak-portal.ts`
- Modify: `web/package.json` (remove `@floating-ui/dom`)
- Test: `web/src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts` (new)

**Interfaces:**
- Consumes: `ak-list-select` (`ListSelect`, custom element `<ak-list-select>`) — it is a normal `HTMLElement`, so `.showPopover()`, `.hidePopover()`, and `.matches(":popover-open")` are available once it has the `popover` attribute.
- Produces: `ak-search-select-view` renders `<ak-list-select popover="auto">` in its shadow DOM. The menu carries `anchor`-based positioning styles; the `<input>` exposes `anchor-name: --ak-search-select-anchor`. Component state `open` (reflected boolean attr) is the single source of truth and is kept in sync with the popover's actual open state via the `toggle` event.

- [ ] **Step 1: Write the failing colocated browser test**

Create `web/src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts`:

```ts
import "./ak-search-select-view";

import type { SearchSelectView } from "./ak-search-select-view";

import type { SelectOptions } from "#elements/types";

import { page } from "@vitest/browser/context";
import { html } from "lit";
import { describe, expect, test } from "vitest";

const LONG_LABEL =
    "The quick brown fox jumps over the lazy dog. She sells seashells down by the sea shore. " +
    "Rubber baby buggy bumpers. What stops x-rays? Even dogs can't. Red fish vanish, then grow bigger.";

const options: SelectOptions<string> = {
    grouped: false,
    options: [
        ["short", "Short label", null],
        ["long", LONG_LABEL, null],
    ],
};

/** Mount a view and return the element + its inner popover menu. */
async function mount(template: unknown) {
    const ctx = page.renderLit(template);
    const view = ctx.container.querySelector<SearchSelectView>("ak-search-select-view")!;
    await view.updateComplete;
    const input = view.renderRoot.querySelector<HTMLInputElement>("input")!;
    const menu = view.renderRoot.querySelector<HTMLElement>("ak-list-select")!;
    return { ctx, view, input, menu };
}

describe("ak-search-select-view anchored popover", () => {
    test("menu is a popover, closed by default", async () => {
        const { menu } = await mount(
            html`<ak-search-select-view .options=${options} blankable></ak-search-select-view>`,
        );

        expect(menu.getAttribute("popover")).toBe("auto");
        expect(menu.matches(":popover-open")).toBe(false);
    });

    test("opening shows the popover in the top layer", async () => {
        const { view, menu } = await mount(
            html`<ak-search-select-view .options=${options} blankable></ak-search-select-view>`,
        );

        view.open = true;
        await view.updateComplete;

        expect(menu.matches(":popover-open")).toBe(true);
    });

    test("menu width matches the input width", async () => {
        const { view, input, menu } = await mount(
            html`<div style="width: 420px">
                <ak-search-select-view .options=${options} blankable></ak-search-select-view>
            </div>`,
        );

        view.open = true;
        await view.updateComplete;

        // anchor-size(width) should size the menu to the input.
        const inputW = input.getBoundingClientRect().width;
        const menuW = menu.getBoundingClientRect().width;
        expect(Math.abs(menuW - inputW)).toBeLessThanOrEqual(2);
    });

    test("is not clipped by an overflow:hidden modal dialog", async () => {
        const { view, menu } = await mount(
            html`<dialog
                open
                style="overflow: hidden; width: 300px; height: 120px; padding: 0;"
            >
                <ak-search-select-view .options=${options} blankable></ak-search-select-view>
            </dialog>`,
        );

        view.open = true;
        await view.updateComplete;

        // A top-layer popover paints above the dialog and is hit-testable at its own
        // coordinates even though the dialog clips its overflow.
        const rect = menu.getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        const probeY = rect.top + Math.min(rect.height - 2, 8);
        const topEl = document.elementFromPoint(midX, probeY);
        expect(menu === topEl || menu.contains(topEl)).toBe(true);
    });

    test("light dismiss syncs `open` back to false", async () => {
        const { view, menu } = await mount(
            html`<ak-search-select-view .options=${options} blankable></ak-search-select-view>`,
        );

        view.open = true;
        await view.updateComplete;
        expect(menu.matches(":popover-open")).toBe(true);

        menu.hidePopover();
        await view.updateComplete;

        expect(view.open).toBe(false);
    });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npx vitest run --project "Browser Tests" src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts`
Expected: FAIL — the menu has no `popover` attribute (`getAttribute("popover")` is `null`), and it is still wrapped in `ak-portal` / gated behind `inputRefIsAvailable`, so `:popover-open` is never true.

- [ ] **Step 3: Remove the portal import and the `inputRefIsAvailable` gate**

In `ak-search-select-view.ts`:

Delete the import line:
```ts
import "#elements/forms/SearchSelect/ak-portal";
```

Delete the `inputRefIsAvailable` state (lines ~222-223):
```ts
// Tracks when the inputRef is populated, so we can safely reschedule the
// render of the dropdown with respect to it.
@state()
protected inputRefIsAvailable = false;
```

Delete the `firstUpdated` override that set it (lines ~249-256), leaving `connectedCallback` intact:
```ts
public override firstUpdated(changed: PropertyValues<this>) {
    super.firstUpdated(changed);

    // Route around Lit's scheduling algorithm complaining about re-renders
    requestAnimationFrame(() => {
        this.inputRefIsAvailable = Boolean(this.#inputRef?.value);
    });
}
```

- [ ] **Step 4: Add anchor-name + popover positioning styles**

In `ak-search-select-view.ts`, extend the `css`\`\`` block inside `static styles` (currently only sets `--pf-c-select__toggle-wrapper--MaxWidth`). Append:

```css
input.pf-c-select__toggle-typeahead {
    anchor-name: --ak-search-select-anchor;
}

ak-list-select[popover] {
    /* Override the UA popover default (fixed + centered) with anchored placement. */
    position: absolute;
    margin: 0;
    inset: auto;
    padding: 0;
    border: 0;
    background: transparent;
    overflow: visible;

    position-anchor: --ak-search-select-anchor;
    top: anchor(bottom);
    left: anchor(left);
    width: anchor-size(width);
    max-height: 40vh;

    /* Flip above the input when there is no room below. */
    position-try-fallbacks: flip-block;
}
```

> The `anchor-name` is a static dashed-ident. Anchor names are scoped to their tree, and each `ak-search-select-view` instance owns its own shadow root (its own tree scope), so a static name cannot collide across instances. `ak-list-select` already caps its internal `.pf-c-dropdown__menu` at `max-height: 50vh` with `overflow-y: auto`, so long lists scroll inside the anchored box.

- [ ] **Step 5: Popover-ize the menu markup**

In `render()`, replace the whole `${this.inputRefIsAvailable ? html\`<ak-portal ...>...</ak-portal>\` : nothing}` block (lines ~510-532) with an always-rendered popover menu:

```ts
            <ak-list-select
                popover="auto"
                id="menu-${this.getAttribute("data-ouia-component-id")}"
                ${ref(this.#menuRef)}
                .options=${this.managedOptions}
                value=${ifDefined(this.value)}
                @change=${this.#changeListener}
                @blur=${this.#blurListener}
                @toggle=${this.#menuToggleListener}
                emptyOption=${ifPresent(emptyOption)}
                actionLabel=${ifPresent(this.actionLabel)}
                @ak-select-action=${this.#actionListener}
                @keydown=${this.#listKeydownListener}
                @keyup=${this.#listKeyupListener}
            ></ak-list-select>`;
```

Note the opening `return html\`<div class="pf-c-select" ...> ... </div>` stays; only the trailing portal expression changes. The `open` local (`const { open } = this;`) is no longer read in the template — remove that destructuring line to avoid an unused-var lint error, or reference it in Step 6's logic instead.

- [ ] **Step 6: Drive the popover from `open`, sync back via `toggle`, and guard reopen**

Replace the `updated()` override (lines ~245-247) and add the sync helper + toggle listener + reopen guard.

Replace:
```ts
public override updated() {
    this.setAttribute("data-ouia-component-safe", "true");
}
```
with:
```ts
public override updated() {
    this.#syncMenuVisibility();
    this.setAttribute("data-ouia-component-safe", "true");
}

/**
 * Reconcile the popover's actual open state with `this.open`.
 * Called from `updated()` so it runs after the menu has rendered.
 */
#syncMenuVisibility() {
    const menu = this.#menuRef.value;
    if (!menu) return;

    const popoverOpen = menu.matches(":popover-open");

    if (this.open && !this.readOnly && !popoverOpen) {
        menu.showPopover();
    } else if ((!this.open || this.readOnly) && popoverOpen) {
        menu.hidePopover();
    }
}
```

Add the toggle listener (near the other `#...Listener` fields):
```ts
/**
 * Reflect browser-driven popover state changes (light dismiss, Esc) back
 * into `this.open`, keeping component state authoritative.
 */
#menuToggleListener = (event: ToggleEvent) => {
    const nowOpen = event.newState === "open";

    if (nowOpen) {
        // Record when the browser closes the popover so a click on the input
        // that *caused* the dismiss doesn't immediately reopen it.
        return;
    }

    this.#lastLightDismiss = event.timeStamp;

    if (this.open) {
        this.open = false;
    }
};

/** Timestamp of the last browser-driven popover close (see reopen guard). */
#lastLightDismiss = -Infinity;
```

Update `#clickListener` (lines ~276-281) so a click that light-dismissed the open menu doesn't reopen it:
```ts
#clickListener = (event: Event) => {
    if (this.readOnly) return;

    // If this same click just light-dismissed the open popover, treat it as a
    // close: leave `open` false instead of toggling it back on.
    const dismissedByThisClick = event.timeStamp - this.#lastLightDismiss < 250;

    this.open = dismissedByThisClick ? false : !this.open;
    this.#inputRef.value?.focus();
};
```

- [ ] **Step 7: Delete `ak-portal.ts` and remove the floating-ui dependency**

```bash
cd web
rm src/elements/forms/SearchSelect/ak-portal.ts
```

Remove the `@floating-ui/dom` line from `web/package.json` `dependencies` (currently `"@floating-ui/dom": "^1.7.6",` at ~line 98). Then refresh the lockfile:
```bash
cd web && pnpm install
```

Verify nothing else imports it:
```bash
cd web && grep -rn "floating-ui\|ak-portal" src test e2e --include="*.ts" | grep -v node_modules
```
Expected: no output.

- [ ] **Step 8: Run the browser test to verify it passes**

Run: `cd web && npx vitest run --project "Browser Tests" src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts`
Expected: PASS (all five tests).

- [ ] **Step 9: Typecheck and lint the changed files**

Run: `cd web && npm run lint:types`
Expected: no errors.

Run: `cd web && npx eslint --fix src/elements/forms/SearchSelect/ak-search-select-view.ts src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts`
Expected: no remaining errors/warnings.

- [ ] **Step 10: Commit**

```bash
cd web && git add src/elements/forms/SearchSelect/ak-search-select-view.ts \
    src/elements/forms/SearchSelect/ak-search-select-view.browser.test.ts \
    package.json pnpm-lock.yaml
git rm src/elements/forms/SearchSelect/ak-portal.ts
git commit -m "web/elements: render search-select menu as anchored popover, drop ak-portal"
```

---

### Task 2: Repoint the e2e `selectSearchValue` fixture

**Files:**
- Modify: `web/e2e/fixtures/FormFixture.ts:185-189`

**Interfaces:**
- Consumes: the Task 1 DOM — options now live in `<ak-list-select>` (a popover) inside the `ak-search-select-view` shadow root, no longer in a `div[data-managed-for]` portal container. Option buttons carry `part="ak-list-select-button"`.
- Produces: an updated `selectSearchValue` that all `test/browser/*` suites depend on (providers, applications, rac).

Current code (lines 185-189):
```ts
const button = this.page
    // ---
    .locator(`div[data-managed-for*="${fieldName}"] button`, {
        hasText: pattern,
    });
```

- [ ] **Step 1: Update the option locator to the popover menu**

Replace the `const button = ...` block with a locator scoped to the `ak-search-select-view` whose input has the matching `name`, then into its `ak-list-select` popover (Playwright CSS locators pierce open shadow roots):

```ts
const button = this.page
    .locator("ak-search-select-view")
    .filter({ has: this.page.locator(`input[name="${fieldName}"]`) })
    .locator("ak-list-select [part='ak-list-select-button']", {
        hasText: pattern,
    });
```

- [ ] **Step 2: Run the providers browser suite (integration verification)**

This suite selects "Signing Key", flows, and certificates inside the New Provider Wizard `<dialog>` — the exact scenario the rework targets.

Run: `cd web && npx vitest run --project "Browser Tests" test/browser/600-providers.test.ts`
Expected: PASS. (Requires a running authentik dev instance per `test/browser/AGENTS.md`; if the suite cannot reach one, note that and defer to Task 3's manual drive.)

- [ ] **Step 3: Run the applications and rac suites**

Run: `cd web && npx vitest run --project "Browser Tests" test/browser/700-applications.test.ts test/browser/800-rac.test.ts`
Expected: PASS.

- [ ] **Step 4: Typecheck and commit**

Run: `cd web && npm run lint:types`
Expected: no errors.

```bash
cd web && git add e2e/fixtures/FormFixture.ts
git commit -m "web/e2e: locate search-select options via anchored popover menu"
```

---

### Task 3: Real-app verification and final checks

**Files:** none (verification only).

- [ ] **Step 1: Build the web UI**

Run: `cd web && npm run build`
Expected: build succeeds with no errors.

- [ ] **Step 2: Drive the real app (the reported scenario)**

With the dev server running, open the Admin UI → Providers → edit an OAuth2/OpenID provider → open the **Signing Key** select (the demo's extraordinarily long dummy string). Confirm, inside the modal `<dialog>`:
- the option list is **not clipped** by the dialog and paints above it;
- the menu **width matches** the input, and the long label **wraps**;
- opening near the viewport bottom **flips** the menu above the input;
- clicking outside and pressing **Esc** both dismiss the menu (and Esc dismisses the menu before the dialog);
- **ArrowDown/ArrowUp** move focus into the list and back.

> If the width is visibly wrong (menu narrower/wider than the field), switch the `anchor-name` from `input.pf-c-select__toggle-typeahead` to the `.pf-c-select` container in Task 1 Step 4 and re-verify — the toggle container, not the raw input, is the visual field width.

- [ ] **Step 3: Verify in Storybook (non-dialog baseline)**

Run: `cd web && npm run storybook`
Open **Elements / Search Select / View Handler** → Default and DescribedGroups. Confirm the dropdown opens, positions below the input, matches width, and closes on outside click.

- [ ] **Step 4: Full lint + type gate**

Run: `cd web && npm run lint-check && npm run lint:types`
Expected: no errors, zero warnings.

- [ ] **Step 5: Commit any verification-driven fixes**

If Step 2 required the anchor-target change (or any tweak), commit it:
```bash
cd web && git add -A
git commit -m "web/elements: anchor search-select popover to toggle container for width match"
```
If no changes were needed, skip this step.

---

## Self-Review

**Spec coverage:**
- "not clipped by dialog / top layer" → Task 1 Steps 4-5 (`popover="auto"`), Task 1 Step 1 test 4, Task 3 Step 2.
- "positions itself smartly / flip" → Task 1 Step 4 (`top: anchor(bottom)`, `position-try-fallbacks: flip-block`), Task 3 Step 2.
- "match input width, wrap long labels" → Task 1 Step 4 (`width: anchor-size(width)`), Task 1 test 3, Task 3 Step 2.
- "delete ak-portal" → Task 1 Step 7.
- "remove floating-ui" → Task 1 Step 7.
- "remove findTopmost from this path" → satisfied by deleting ak-portal (its only use here); `findTopmost` itself stays for `MessageContainer`.
- "remove inputRefIsAvailable rAF dance" → Task 1 Step 3.
- "popover=auto light dismiss + restore outside-click-close" → Task 1 Steps 5-6.
- "reopen guard" → Task 1 Step 6 (`#lastLightDismiss` + `#clickListener`).
- "toggle event syncs open" → Task 1 Step 6 (`#menuToggleListener`), test 5.
- "update OUIA/test hooks" → Task 2 (fixture repointed off `data-managed-for`).
- "no Firefox fallback" → not implemented, by design (Global Constraints).
- "verification via providers demo + storybook" → Task 3.

**Placeholder scan:** none — every code step shows the actual code; every run step shows the command and expected result.

**Type consistency:** `#menuRef` is `Ref<ListSelect>` (unchanged); `showPopover`/`hidePopover`/`matches` are `HTMLElement` methods. `#menuToggleListener` typed against `ToggleEvent`. `#lastLightDismiss: number`. `#clickListener` signature widened from `(_ev: Event)` to `(event: Event)` (the param is now read). Names used in tests (`open`, `renderRoot`, `updateComplete`) are all existing public/inherited members of `SearchSelectView`.
