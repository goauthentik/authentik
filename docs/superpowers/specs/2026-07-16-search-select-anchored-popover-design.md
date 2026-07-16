# ak-search-select: anchored popover (no portal)

**Date:** 2026-07-16
**Status:** Approved (design)
**Area:** `web/` — `src/elements/forms/SearchSelect/`

## Problem

`ak-search-select`'s dropdown menu is positioned by `ak-portal`, which physically
moves the `ak-list-select` menu out of the component and appends it to whatever
`findTopmost()` returns (the last open `<dialog>`, else `document.body`), then
positions it with `@floating-ui/dom` (`position: fixed`, `z-index: 9999`, plus an
`autoUpdate` loop).

authentik recently adopted native `<dialog>` modals. A modal `<dialog>` renders in
the browser's **top layer** and its content region is `position: fixed` with
`overflow: hidden`. That makes the portal approach fiddly: a `position: fixed`
menu with `z-index: 9999` is *not* guaranteed to paint above a top-layer dialog,
and the dialog's clipping/containing-block behavior fights the floating menu. The
result is a dropdown that can be clipped or mis-stacked inside modals.

`ak-search-select-view` is the **only** consumer of `ak-portal`, and `ak-portal`
is the only consumer of `findTopmost()` and `@floating-ui/dom` on this path.

## Goal

An MVP that demonstrates the option list:

1. **is not clipped** by the dialog container (escapes `overflow: hidden` and
   stacks above a modal `<dialog>`), and
2. **positions itself smartly** relative to the input (below by default, flips
   above when there's no room), and
3. **matches the input's width**, wrapping long option labels.

…using **no external positioning library** — native Popover API + CSS anchor
positioning only. Firefox lacks CSS anchor positioning today; per the owner's
call we ship without a fallback and revisit only if Firefox proves unacceptable.

## Approach

Render `ak-list-select` as an **anchored popover** directly in
`ak-search-select-view`'s shadow DOM. No DOM surgery, no separate portal element.

- The **Popover API** (`popover` attribute) puts the menu in the top layer,
  which is what actually solves the dialog clipping/stacking problem —
  independent of how the menu is positioned.
- **CSS anchor positioning** (`anchor-name` / `position-anchor` / `position-area`
  / `position-try-fallbacks` / `anchor-size`) handles placement and sizing,
  entirely in CSS.

There is in-repo precedent for exactly this pairing in
[`CardMenu.ts`](../../../web/src/user/LibraryApplication/CardMenu.ts) (popover +
inline `anchor-name`/`position-anchor`, feature-detected via
`CSS.supports("position-anchor", "--test")`).

## What gets deleted

- `web/src/elements/forms/SearchSelect/ak-portal.ts` (the whole element).
- The `@floating-ui/dom` import/usage on this path (and the dependency, if this
  is its last user — verify during planning).
- The `findTopmost()` dependency from this path.
- `inputRefIsAvailable` + its `requestAnimationFrame` dance in
  `ak-search-select-view` — it only existed so the portal could be handed an
  anchor element after first paint. With the menu living in the same shadow root,
  it's no longer needed.

## What replaces it (in `ak-search-select-view`)

### Markup / anchoring

1. The `<input>` gets a unique anchor name:
   `anchor-name: --ak-search-select-anchor-<id>`. Anchor names are tree-scoped to
   the shadow root; input and menu share a shadow root, so scoping is automatic.
   The `<id>` suffix (from the existing OUIA component id) just guards against
   future refactors that might colocate multiple instances.
2. `<ak-list-select>` stays where it's declared in the shadow DOM but gains the
   `popover` attribute (value `auto` — see Open/close).

### Positioning (CSS on the menu)

```css
position: absolute;                          /* popover default; anchor drives insets */
position-anchor: --ak-search-select-anchor-<id>;
position-area: block-end span-inline-end;    /* below the input, inline-start-aligned */
position-try-fallbacks: flip-block;          /* flip above when no room below */
width: anchor-size(width);                   /* match the input's width */
max-height: 40vh;                            /* scroll inside; flip covers the rest */
margin: 0;                                   /* reset UA popover margins */
inset: auto;                                 /* let anchor positioning own insets */
```

Long labels wrap inside the anchor-width menu.

> Note: `position-area` naming/axis keywords are finicky across engine versions;
> the exact keyword set is validated against Chrome during implementation. Intent:
> menu sits directly below the input, left edges aligned, flipping above near the
> viewport bottom.

### Open / close

- `popover="auto"` — gives **light dismiss** (click-outside closes) and
  **Esc-to-close** for free. This also restores outside-click-close, which is
  currently broken: the blur listener in `ak-search-select-view` is commented out
  with a "Disabled while debugging" TODO.
- `this.open` drives `showPopover()` / `hidePopover()` from `updated()`.
- Listen for the popover `toggle` event to sync `this.open` back to `false` when
  the browser light-dismisses the menu, keeping component state consistent.
- **Reopen guard:** clicking the input while the menu is open fires light-dismiss
  *then* the input's click-toggle, which would immediately reopen it. Guard by
  ignoring a toggle-driven reopen that originates from a pointerdown on the anchor
  (standard small guard; exact mechanism finalized in implementation).

### Untouched

- Keyboard behavior (arrow into list, Esc back to input, Tab handling). Focus can
  move into a popover freely, so the existing menu/input focus juggling still
  works.
- The `ak-list-select` component itself, the options/value data flow, and the
  search/filter logic.

## Test / tooling impact

- OUIA hooks tied to the portal go away: `data-ouia-component-type="ak-portal"`,
  `data-managed-by="ak-portal"`, `data-managed-for=<name>`. Any e2e/unit/Storybook
  references get repointed at `ak-list-select[popover]` (or a stable part/id on the
  menu). Enumerate actual references during planning before removing anything.
- Existing `ak-search-select` / `ak-search-select-view` Storybook stories are the
  simple-case verification surface.

## Verification

- **Real app:** providers page → edit a provider → open the "Signing Key" select
  (contains an extraordinarily long dummy string) inside the modal `<dialog>`.
  Confirm: not clipped by the dialog; flips above near viewport bottom; width
  matches the input; long label wraps; click-outside and Esc dismiss; arrow-key
  navigation into the list works.
- **Storybook:** the `ak-search-select-view` stories for a non-dialog baseline.

## Non-goals

- A general reusable `ak-popover` primitive (SearchSelect refactor is a separate,
  longer-term effort; extract later if a second consumer appears).
- A Firefox positioning fallback (revisit only if needed).
- Changing `ak-list-select`, the options data model, or search semantics.
