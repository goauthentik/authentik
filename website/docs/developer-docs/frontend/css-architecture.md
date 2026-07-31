---
title: CSS architecture
sidebar_label: CSS architecture
description: How authentik's runtime CSS and design tokens fit together across the theme package, the document cascade, and Lit components.
---

<!-- cspell:words DTCG Styleframe -->

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
    --pf-global--primary-color--100: var(--ak-color-primary, var(--pf-global--primary-color--100));
    --pf-global--spacer--md: var(--ak-space-md, var(--pf-global--spacer--md));
}
```

Each PatternFly variable falls back to its own prior value, so the bridge only overrides where a token exists. It is imported in two places — `global/theme/variables.css` for the document, and `shadow/patternfly-base.css` for shadow roots — so both cascades resolve the same way.

## Shadow DOM API

Custom properties are the configuration surface:

```css
ak-flow-executor {
    --ak-color-primary: oklch(62% 0.2 260);
}
```

`::part()` is for exposed structure, and only where a brand can reasonably style that substructure without coupling to internal DOM:

```css
ak-flow-executor::part(locale-select) {
    display: none;
}
```

Slots are for composition, not styling.

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
