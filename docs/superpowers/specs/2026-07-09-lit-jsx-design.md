# lit-jsx: JSX for Lit templates in the authentik web UI

**Date:** 2026-07-09
**Status:** Approved (pending spec review)
**Package:** `@goauthentik/lit-jsx` (`packages/lit-jsx`)

## Goal

Let web UI templates be written in JSX instead of `html``` tagged literals, with:

- **Named imports as the component reference.** `import { AppIcon } from "#elements/AppIcon"` both registers the element (module evaluation runs `@customElement`) and provides a typed, refactor-safe tag: `<AppIcon />`. This replaces the fragile side-effect import pattern (`import "#elements/AppIcon"`).
- **React-familiar ergonomics** (`onClick`, `className` accepted) without React's blind spots (hyphenated custom events like `ak-change` are first-class).
- **Correct Lit binding semantics** derived from ground truth (`elementProperties` metadata), not value-type guessing.
- **Gradual adoption.** JSX output is a Lit `TemplateResult`; it interops with `html``` in both directions. Existing code keeps working unmodified; migration is opportunistic, file by file.

## Architecture decision

**Runtime-first hybrid (the React model).** The compile step is esbuild/tsc's built-in automatic JSX transform (`"jsx": "react-jsx"`, `"jsxImportSource": "@goauthentik/lit-jsx"`) — zero custom compiler code. All semantics live in the runtime package.

Rejected alternatives:

- *Custom compile-time transform emitting `html``` directly*: cannot resolve class-as-tag (`<AppIcon />` → `"ak-app-icon"` requires the live `customElements` registry) and cannot read `elementProperties`. Large edge-case surface (dynamic tags, spreads, conditional attrs) — the swamp that sank round one. Retained only as a **future static-subset precompiler optimization**, for which this package's test suite doubles as the conformance spec.
- *Reusing `@types/react`*: rejects `onAkChange`, misrepresents `JSX.Element`, imports React DOM baggage.
- *Direct DOM creation / `createRoot` (the `@chnicoloso/lit-jsx` prior art)*: strays from Lit's render model; explicitly out of scope, along with element registries and lit re-exports.

## Package shape

Rebuilt from scratch in TypeScript (replacing the current JS + hand-written `.d.ts`), following the truncator pattern: `src/` → tsc → `dist/`, with a `prepare` script so workspace consumers always find a built `dist/` (this dissolves the tsconfig chicken/egg — `jsxImportSource` self-resolution works via Node self-referencing exports once `prepare` has run).

Exports:

| Entry | Contents |
| --- | --- |
| `./jsx-runtime`, `./jsx-dev-runtime` | `jsx`, `jsxs`, `jsxDEV`, `Fragment`, and the `JSX` namespace types. What `jsxImportSource` resolves. |
| `.` | Public API: prop-mapping core (`mapElementProps`, `resolveEventName`, prefix resolution), `Fragment`, `FC`, and public types. |

`web/src/elements/utils/unsafe.ts` becomes a thin consumer of the prop-mapping core; `StrictUnsafe` keeps its name and strictness as the server-provided-tag-name entry point.

## Runtime semantics

`jsx(type, props)` dispatches on `type`:

1. **Custom element constructor** (`type.prototype instanceof HTMLElement`): tag name via `customElements.getName(type)`; throws a descriptive error if unregistered. Props resolved against the constructor's `elementProperties` (the `resolvePrefix`/`resolvePropertyName` logic from `unsafe.ts` moves into this package): `attribute: false` → `.prop`, `type: Boolean` → `?attr`, `type: String` → attr, custom attribute names honored.
2. **Function component**: called as `type(props)`, `children` inside props (standard automatic-runtime shape).
3. **String intrinsic** (`div`, `ak-app-icon`): assembled via `lit/static-html.js`; Lit's static-template keying caches per tag.

**Template assembly:** `class`, `style`, and `ref` get dedicated bindings in the assembled template so the `classMap`, `styleMap`, and `ref` directives work. All other props flow through the open-wc `spread` directive.

- `class` additionally accepts `string | string[] | Record<string, boolean>`, normalized by the runtime.
- Directive values in arbitrary *other* props are a **documented limitation** (the spread directive cannot host directives). `null`/`undefined` values are skipped/removed by spread, covering the `ifDefined` use case.

**Events:** props matching `on[A-Z]*` → strip `on`, look up the lowercased remainder in a table generated from `GlobalEventHandlersEventMap` (`onDblClick` → `dblclick`), otherwise acronym-aware kebab-case (`onAkChange` and `onAKChange` both → `ak-change`) → bound as `@event`.

**Aliases:** `className` → `class`, `htmlFor` → `for` (the DOM names are also accepted directly — JSX does not reserve them).

**`key`:** accepted and ignored; Lit's `repeat` directive owns keyed rendering. Documented.

**Children:** passed through untouched — Lit already renders strings, numbers, `TemplateResult`s, arrays, and `nothing`.

**Fragment:** returns its children (array-normalized).

## Types

Authored `JSX` namespace, no `@types/react`:

- `JSX.Element` = `SlottedTemplateResult`. The type-level vocabulary this package needs (`SlottedTemplateResult`, `TemplatedProperties`, `LitPropertyRecord`) moves *into* the package — it cannot depend on `web/` — and `web/src/elements/types.ts` re-exports them so existing imports keep working.
- `JSX.IntrinsicElements`: mapped type over `HTMLElementTagNameMap` — global + element-specific attributes plus `on*` handler props generated from event-map types. `ak-*` registrations get `TemplatedProperties`-style prop typing automatically.
- **Class-as-tag** via `JSX.LibraryManagedAttributes`: constructor ↦ `TemplatedProperties<InstanceType<C>>` + event handler props. This is where round one drowned, so it gets the densest test coverage.
- `FC<P>`: this package's function-component type (children-in-props). **`LitFC` in `web/src/elements/types.ts` is unchanged** — all ~15 existing `LitFC` components destructure props only, so they remain callable both as plain functions and as JSX tags; they migrate to `FC` opportunistically.

## Testing (TDD; vitest is the guiding light)

Two vitest projects inside the package:

- **node** (fast inner loop): event-name resolution, prop-prefix resolution against mock `elementProperties`, class normalization, and type-level tests — `expectTypeOf` positives plus `@ts-expect-error` negatives (wrong prop type, unknown event name, unregistered element class, constructor that isn't an element).
- **browser** (Playwright Chromium, mirroring `web/`'s existing setup): real `@customElement` fixtures rendered with Lit's `render()` — attributes/properties/booleans land correctly, events dispatch to handlers, re-renders update elements in place rather than re-creating them, JSX-inside-`html```-inside-JSX interop.

Tests are `.tsx` and exercise the real transform end-to-end via the package's own tsconfig (`"jsx": "react-jsx"`, `"jsxImportSource": "@goauthentik/lit-jsx"`).

## Gradual migration (hard constraint)

Existing code continues to work at every step; nothing is bulk-renamed.

1. **Package lands standalone.** No `web/` changes required for it to merge; nothing in `web/` depends on it yet.
2. **`web/` opts in**: tsconfig gains `jsx`/`jsxImportSource` (esbuild honors them natively — no build-system changes). `.ts` and `.tsx` files coexist indefinitely; only files renamed to `.tsx` can use JSX, and renaming is per-file and opt-in.
3. **`unsafe.ts` refactor**: internals delegate to the package's prop-mapping core; `StrictUnsafe`'s public signature is unchanged.
4. **Pilot migrations**: 2–3 leaf templates with good existing test coverage, chosen to exercise class-as-tag, custom events, and function components.
5. Broader migration proceeds opportunistically when touching surrounding code — same policy as the i18n message-ID migration.

Out of scope: SSR/`@lit-labs/ssr`, the static-subset precompiler (future optimization), any change to how elements are authored (`@customElement` + Lit stays).

## Risks

- **`customElements.getName()`** requires the element to be registered before first render; named imports guarantee module evaluation, but lazy/conditional registration patterns would throw. The error message must name the class and suggest the fix.
- **Spread-directive fidelity**: the open-wc `spread` directive is the weakest dependency (event listener grooming, property removal). Browser tests cover its behavior; if it falls short we own a fork (the prior art already demonstrates the fix).
- **Type-level complexity**: `LibraryManagedAttributes` over constructors is intricate; mitigated by making type tests first-class TDD artifacts rather than an afterthought.
