---
title: CSS architecture
sidebar_label: CSS architecture
description: How authentik's runtime CSS and design tokens fit together across the theme package, the document cascade, and Lit components.
---

authentik's UI is a customized PatternFly 4 system wrapped in Lit web components. Treat PatternFly as a compatibility layer, not the public API to build on: the stable surface is the `--ak-*` token set.

## The pieces

- **`@goauthentik/theme`** owns the design tokens. Token modules are written in TypeScript, compiled by [Styleframe](https://styleframe.dev), and emitted as CSS custom properties plus a [DTCG](https://www.designtokens.org/) document.
- **`@goauthentik/fonts`** ships every typeface and its `@font-face` rules, separately from the tokens because they change on a different cadence. `faces.css` holds the RedHat brand text faces; `icons.css` holds the `pficon` and Font Awesome faces the PatternFly icon classes render glyphs from.
- **`web/src/styles/global/theme/token-bridge.css`** maps the semantic tokens onto the PatternFly variables that existing component CSS already reads.
- **`web/src/styles/`** assembles all of it into the three document bundles and the two per-shadow-root sheets. See [Cascade layers](./cascade-layers.md).
- **`web/src/elements/Base.ts`** adopts the shared sheets into every component's shadow root; `web/src/common/stylesheets.ts` centralizes `CSSStyleSheet` creation.

## Token tiers

| Tier            | Prefix                | Stability          | Use                                        |
| --------------- | --------------------- | ------------------ | ------------------------------------------ |
| Primitive       | internal or generated | private            | palette stops, raw scales, build input     |
| Semantic        | `--ak-*`              | public             | custom CSS, component styles, docs         |
| Component-local | `--_*` or `--ak-c-*`  | private by default | implementation detail inside one component |

Semantic names express a design decision, not a raw value:

```css
:root {
    --ak-color-primary: oklch(0.518 0.1725 259.3 / 1); /* #0066cc */
    --ak-color-surface: oklch(1 0 0 / 1); /* #ffffff */
    --ak-space-md: 1rem;
    --ak-radius-sm: 3px;
}
```

Do not promote component property names into the public surface:

```css
/* Avoid */
--ak-c-button-primary-background-color-hover-padding-left: 1rem;
```

## The token pipeline

Tokens are authored as typed modules under `packages/theme/src/tokens/`, one per category. Styleframe evaluates them into a variable tree, and the package build emits several shapes of the same data:

```text
packages/theme/src/tokens/*.ts        typed token modules
  -> Styleframe                       variable tree
  -> dist/index.css                   every token, one file
  -> dist/{color,typography,...}.css  per-category slices
  -> dist/dtcg/tokens.json            DTCG interchange for design tooling
```

Colors are authored as hex and transformed to `oklch()` on the way out, each carrying the original hex in a trailing comment so editors still render a swatch.

DTCG is interchange data for tooling — Figma sync, validation, generated documentation. It is not a runtime format. The browser consumes CSS custom properties; keep runtime styling decoupled from the DTCG document.

## The PatternFly bridge

Most component CSS still reads `--pf-*`. `token-bridge.css` maps the semantic layer onto those names, so existing CSS keeps working while new CSS targets the shorter surface:

```css
:root,
:host {
    --pf-global--primary-color--100: var(--ak-color-primary, oklab(0.522 -0.0434 -0.1717));
    --pf-global--spacer--md: var(--ak-space-md, 1rem);
}
```

Each PatternFly variable falls back to a literal copy of its prior value, so the bridge only overrides where a token exists. The fallback must be a literal: a self-reference like `var(--ak-space-md, var(--pf-global--spacer--md))` is a custom-property dependency cycle, which computes to invalid rather than the prior value. The bridge is imported in two places — `global/theme/variables.css` for the document, and `shadow/patternfly-base.css` for shadow roots — so both cascades resolve the same way.

## Styling components

A component exposes three styling surfaces, in order of preference: custom properties, host attributes, and parts.

**Custom properties are the configuration surface:**

```css
ak-flow-executor {
    --ak-color-primary: oklch(62% 0.2 260);
}
```

**Variants are host attributes, styled with `:host([attribute])`.** A component's visual states — position, size, expanded, resizable — belong on the host element as attributes, with the styling keyed off them inside the shadow root:

```css
:host([position="left"]) .ak-v2-c-drawer__panel {
    inset-inline-start: 0;
}
```

The variant API stays visible in markup (`<ak-drawer position="left">` documents itself), consumers and tests can target states without knowing shadow internals, and the component avoids maintaining a parallel class vocabulary for its own states.

**Prefer reassigning custom properties over writing alternative concrete stylings.** When a variant only changes values — a width, a color, a shadow — the variant rule should reassign the component-local properties the base rules consume, not repeat the declaration block with different literals:

```css
.ak-v2-c-drawer__panel {
    box-shadow: var(--ak-v2-c-drawer__panel--BoxShadow);
}

:host([position="left"]) {
    --ak-v2-c-drawer--m-expanded__panel--BoxShadow: var(--_drawer-shadow-right);
}
```

One rule owns the layout; variants are data. Reserve separate rule blocks for variants that genuinely change structure.

**Slots are for composition; ownership decides what is slotted.** Content goes in a slot when the consumer owns it — actions, footers, arbitrary body content. It stays in the template when the component owns it — icons, labels bound to properties, structure the component must control to function. A slot is not a styling escape hatch: if the only reason to slot something is to reach it with outside CSS, expose a custom property or a part instead.

**`::slotted()` is a boundary tool — keep it shallow.** It can only select the slotted elements themselves, never their descendants, and it should only declare what a container legitimately owns about its children: layout, spacing, alignment.

```css
::slotted(*) {
    margin-block: 0;
}
```

Typography and color inside slotted content belong to the document cascade — slotted elements are light DOM, so the global stylesheets and semantic tokens already reach them. If a component needs deep control over slotted content, that content is probably component-owned and should move into the template.

**`::part()` is for exposed structure**, and only where a brand can reasonably style that substructure without coupling to internal DOM:

```css
ak-flow-executor::part(locale-select) {
    display: none;
}
```

## Accessibility defaults

New component CSS should support `color-scheme: light dark`, `accent-color`, `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`, `forced-colors`, and logical properties for right-to-left layouts.

Prefer semantic tokens that media queries adjust over separate per-variant theme files. Document-level light/dark, contrast, and motion overrides belong in `web/src/styles/global/mode/`.

## Guardrails

- Keep the public semantic set at roughly 30 to 60 names until real user needs justify more.
- Do not expose every CSS property as a public token.
- Do not document `--ak-c-*` as stable unless it is intentionally promoted.
- Do not generate tokens from PatternFly variable names.
- Keep part names short and structural: `control`, `label`, `icon`, `content`, `footer`.
- Keep direct custom CSS injection an advanced escape hatch, not the primary theming API.

## Still to do

- Derive relational colors (hover, tint, and shade variants) algorithmically in OKLCH space instead of hand-picking each value. Colors already emit as `oklch()`, so lightness and chroma are directly adjustable; today every variant is still an explicit stop.
- Migrate component markup off PatternFly incrementally, starting where styling is already mostly custom.
- Move component CSS next to the component it styles, rather than under `web/src/styles/authentik/components/`.
- Generate token reference documentation from the DTCG export instead of maintaining the table by hand.
- Offer live previews of token-level brand customization in the product.

## External references

- [Design Tokens Community Group](https://www.designtokens.org/)
- [Design Tokens Format Module](https://www.designtokens.org/tr/2025.10/format/)
- [Styleframe](https://styleframe.dev)
- [PatternFly tokens](https://www.patternfly.org/tokens/about-tokens/)
- [MDN: cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer)
