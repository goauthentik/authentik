---
title: CSS architecture
sidebar_label: CSS architecture
description: Proposed runtime CSS and design token architecture for authentik's Lit web components.
---

<!-- cspell:words DTCG unlayered -->

authentik's UI is currently a customized PatternFly 4 system wrapped by Lit web components. Treat PatternFly as the compatibility substrate, not the future public API.

## Current state

- `web/package.json` depends on `@patternfly/patternfly` 4.x and `@patternfly/elements`.
- `web/src/elements/Base.ts` injects PatternFly base CSS, component CSS, and authentik base CSS into each Lit element.
- `web/src/common/stylesheets.ts` centralizes `CSSStyleSheet` creation and adopted stylesheet updates.
- `web/src/styles/authentik/base/*.css` overrides PatternFly global variables and already contains light and dark theme branches.
- Brand custom CSS is appended to component style roots, including nested shadow roots.
- Components mix PF class markup, PF per-component imports, global CSS, inline styles, `part` attributes, and local `--ak-*` variables.

This gives good incremental control, but no stable external theming contract. Users have to inspect `--pf-*` and internal `--ak-c-*` names, then hope those names survive upgrades.

## Direction

Split the design system into two independent layers:

1. Runtime CSS architecture: browser-native CSS variables, Shadow DOM inheritance, CSS parts, slots, container queries, media queries, and eventually cascade layers.
2. Token pipeline: DTCG-format JSON as interchange data, compiled to CSS variables and other outputs by a build tool.

Do not couple runtime styling to DTCG. The browser should consume CSS variables. DTCG should remain source data for tooling, Figma sync, validation, and docs.

## Public token tiers

Use three token tiers:

| Tier            | Prefix                | Stability          | Use                                        |
| --------------- | --------------------- | ------------------ | ------------------------------------------ |
| Primitive       | internal or generated | private            | palette stops, raw scales, build input     |
| Semantic        | `--ak-*`              | public             | custom CSS, component styles, docs         |
| Component-local | `--_` or `--ak-c-*`   | private by default | implementation detail inside one component |

Prefer short semantic names:

```css
:root {
    --ak-color-primary: #3b82f6;
    --ak-color-surface: white;
    --ak-color-text: #18181b;
    --ak-space-md: 1rem;
    --ak-radius-sm: 3px;
}
```

Avoid exposing component property names as the main customization API:

```css
/* Avoid */
--ak-c-button-primary-background-color-hover-padding-left: 1rem;
```

## Runtime layering

Target cascade order:

```css
@layer reset, base, tokens, components, utilities, overrides;
```

Use layers only after the active CSS entrypoints can establish a single layer order. PatternFly CSS and existing unlayered rules should stay outside layers until their order is audited. In CSS, unlayered normal declarations override layered normal declarations, so partially layering token files can silently lose to legacy declarations.

Recommended meaning:

- `reset`: minimal browser normalization.
- `base`: document, typography, default color scheme, accessibility defaults.
- `tokens`: semantic `--ak-*` values and theme variants.
- `components`: reusable component class and shadow styles.
- `utilities`: narrow one-purpose utilities.
- `overrides`: brand custom CSS and targeted escape hatches.

## Shadow DOM API

Use custom properties for configuration:

```css
ak-flow-executor {
    --ak-color-primary: oklch(62% 0.2 260);
}
```

Use `::part()` only for exposed structure:

```css
ak-flow-executor::part(locale-select) {
    display: none;
}
```

Use slots for composition, not styling. A component should expose stable parts only when a user or brand can reasonably style that substructure without coupling to internal DOM.

## Accessibility defaults

New component CSS should support:

- `color-scheme: light dark`
- `accent-color: var(--ak-color-accent)`
- `prefers-color-scheme`
- `prefers-reduced-motion`
- `prefers-contrast`
- `forced-colors`
- logical properties for localization and right-to-left layouts

Avoid baking accessibility variants into separate theme files. Prefer semantic tokens that media queries can adjust.

## Token pipeline

DTCG 2025.10 is the right interchange target, but not yet a frictionless runtime source. The spec uses token objects with `$value` and `$type`, recommends `.tokens` or `.tokens.json`, and supports token references such as `{colors.blue}`. Style Dictionary has DTCG support in v4, but its own docs currently note that full support for the 2025.10 format is still work in progress for v5.

Recommended build pipeline:

```text
DTCG tokens
  -> validation
  -> Style Dictionary or equivalent compiler
  -> generated CSS variables
  -> imported runtime token CSS
  -> Lit component styles and brand custom CSS
```

Start with handwritten runtime CSS tokens. Add generated files only when token ownership, review workflow, and Figma sync are defined.

## Migration phases

1. Establish public `--ak-*` semantic tokens mapped to current PF values.
2. Update custom CSS docs to prefer `--ak-*` over `--pf-*`.
3. Migrate new or touched authentik components to consume semantic tokens first, PF globals second.
4. Add token metadata docs generated from the public token list.
5. Introduce DTCG source files and a compiler when the public token list is stable.
6. Add cascade layers after global, shadow, and custom CSS order are audited.
7. De-PF component markup incrementally, starting with components whose styling is already mostly custom.

## Guardrails

- Public semantic tokens should stay near 30 to 60 names until real user needs justify more.
- Do not expose every CSS property as a public token.
- Do not document `--ak-c-*` as stable unless it is intentionally promoted.
- Do not generate tokens directly from PatternFly variable names.
- Keep component part names short and structural, for example `control`, `label`, `icon`, `content`, `footer`.
- Keep direct custom CSS injection as an advanced escape hatch, not the primary theming API.

## External references

- [Design Tokens Community Group](https://www.designtokens.org/)
- [Design Tokens Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/)
- [Style Dictionary DTCG support](https://styledictionary.com/info/dtcg/)
- [PatternFly tokens](https://www.patternfly.org/tokens/about-tokens/)
- [PatternFly token usage](https://www.patternfly.org/tokens/develop-with-tokens/)
- [NL Design System token convention](https://nldesignsystem.nl/handboek/developer/design-token-conventie/)
- [GC Design System design tokens](https://design-system.canada.ca/en/styles/design-tokens/)
- [MDN cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer)
