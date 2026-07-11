# @goauthentik/lit-jsx

JSX runtime for Lit templates. JSX expressions evaluate to Lit
`TemplateResult`s, so they interoperate with `html``` in both directions and
render through Lit exactly like hand-written templates.

## Setup

```jsonc
// tsconfig.json
{
    "compilerOptions": {
        "jsx": "react-jsx",
        "jsxImportSource": "@goauthentik/lit-jsx",
    },
}
```

esbuild, Vite, and tsc all honor these settings; no compiler plugin is
involved.

## Usage

```tsx
import { AppIcon } from "#elements/AppIcon";

// The named import registers the element AND provides a typed tag.
const template = (
    <AppIcon
        name="applications"
        size={24}
        class={["pf-m-lg", { "pf-m-active": active }]}
        onAkChange={(event) => console.log(event)}
    />
);
```

## Semantics

- **Class tags**: `<AppIcon />` resolves its tag name via
  `customElements.getName()`. The class must be registered (importing its
  module does that) or rendering throws.
- **Props**: declared Lit reactive properties bind following lit's own
  defaults — a `@property()` declaration without an `attribute` key still
  binds as an attribute (`type: Boolean` → boolean attribute, custom
  attribute names honored); only an explicit `attribute: false` binds as a
  property. Undeclared props fall back to: `value`/`checked`/`selected` →
  property; booleans → boolean attribute; objects/functions → property;
  other primitives → attribute.
- **Events**: resolved through a hand-authored map covering the full DOM
  event set, completeness-verified at the type level (a `satisfies` clause
  plus a type test that every `GlobalEventHandlersEventMap` name is
  covered) — `onClick` → `click`, `onBeforeMatch` → `beforematch`,
  `onCommand` → `command`, `onPointerRawUpdate` → `pointerrawupdate`, and so
  on. Names outside that map kebab-case, so `onAkChange` → `ak-change`. No
  casing surprises: the runtime map and the JSX event-handler types share one
  source of truth.
- **Intrinsic `ak-*` tag names** resolve `elementProperties` only when the
  element is registered in `customElements` at render time. An unregistered
  tag name falls back to the undeclared-prop heuristics above silently;
  an unregistered **class** tag (`<AppIcon />`) throws instead (see Class
  tags, above).
- **`class`** accepts strings, numbers, arrays, records (clsx-style), or the
  `classMap` directive. Falsy values — `false`, `null`, `undefined`, `0`,
  `NaN` — are dropped, same as clsx. `className` and `htmlFor` are accepted
  aliases.
- **`style`** accepts a string, a `styleMap`-compatible object, or the
  `styleMap` directive. **`ref`** takes Lit's `RefOrCallback`.
- **Children**: strings, numbers, templates, arrays; `true`/`false`/`null`/
  `undefined` render nothing.

## Limitations

- Directive values (e.g. `ifDefined`, `live`) are only supported on `class`,
  `style`, and `ref`. Elsewhere, pass `undefined`/`null` to omit a binding —
  the spread path removes it.
- `key` is accepted and ignored; use Lit's `repeat` directive for keyed
  lists.
- No SSR (`@lit-labs/ssr`) support.
