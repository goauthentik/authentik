---
title: Cascade layers
sidebar_label: Cascade layers
description: A staged plan for adopting CSS @layer in authentik's web UI without breaking the existing cascade.
---

<!-- cspell:words unlayered -->

This page is a working proposal. The goal is to discuss the migration before any rules move into layers, because partial layering can quietly reduce predictability rather than improve it.

## Why we want layers

Two recurring problems motivate this:

1. **Brand custom CSS is hard to reason about.** Today it is adopted into each shadow root after authentik's own styles, but specificity duels still force users toward `!important`. A dedicated `overrides` layer at the end of the cascade would make user CSS reliably win without specificity wars.
2. **Component styles and PatternFly compatibility CSS sit in the same bucket.** When the PF base, the authentik base, and per-component styles all live at the same cascade level, ordering depends on adoption order and import order. Layers let us name that ordering explicitly.

## Why we have not done it yet

CSS layers have one rule that makes partial adoption dangerous:

> Unlayered author rules outrank layered normal rules.

Today every authentik and PatternFly rule is unlayered. The moment we wrap any rule in `@layer components { ... }`, that rule loses to every unlayered rule, even ones with lower specificity. A partial migration silently demotes whatever we layer first.

## Target cascade order

```css
@layer reset, base, tokens, components, utilities, overrides;
```

| Layer        | Contains                                                              |
| ------------ | --------------------------------------------------------------------- |
| `reset`      | Browser normalization.                                                |
| `base`       | Document defaults, typography, color-scheme, accessibility baselines. |
| `tokens`     | `--ak-*` semantic tokens, theme variants, reduced-motion overrides.   |
| `components` | PatternFly base, authentik base, per-component styles.                |
| `utilities`  | Narrow, single-purpose helpers (`.sr-only`, `.ak-fade-in`).           |
| `overrides`  | Brand custom CSS and explicit escape hatches loaded last.             |

## Current state, mapped to those layers

| Today's location                                                                       | Future layer   |
| -------------------------------------------------------------------------------------- | -------------- |
| PatternFly `patternfly-common.css`, `-globals.css`                                     | `reset`+`base` |
| `web/src/styles/authentik/base/{fonts,globals,scrollbars,placeholder}.css`             | `base`         |
| `web/src/styles/authentik/base/tokens.css` (generated) and `token-bridge.css`          | `tokens`       |
| `web/src/styles/authentik/base.css` + components/                                      | `components`   |
| PatternFly per-component CSS imported in components                                    | `components`   |
| `web/src/styles/authentik/base/common.css` utilities (`.sr-only`, `.ak-fade-in`, etc.) | `utilities`    |
| Brand `branding_custom_css`, applied per shadow root in `Base.ts`                      | `overrides`    |

Nothing here is wrong; it just is not named.

## Two cascade contexts to think about separately

authentik has two distinct cascade contexts and they don't interact:

1. **Document cascade.** Driven by `interface.global.css`, `flows.global.css`, `static.global.css`. Loads PatternFly, fonts, tokens, globals, locale CSS.
2. **Per-shadow-root cascade.** Each Lit element adopts `PFBase`, `AKBase`, its own component CSS, and brand custom CSS via `Base.ts`.

These cascades are independent. Layers in one have no effect in the other. We can adopt layers in one context without disturbing the other.

## Proposed migration

### Step 0 — Reserve the layer order

Add a single `@layer` declaration at the top of the document entrypoints and at the top of the per-shadow-root base sheets. **No rule moves into a layer yet.** This is a zero-behavior change that lets downstream PRs reference a stable order.

```css
/* interface.global.css, flows.global.css, patternfly/base.css */
@layer reset, base, tokens, components, utilities, overrides;
```

### Step 1 — Move brand custom CSS into `@layer overrides`

Only viable once everything else is layered, because of the unlayered-beats-layered rule. So this is the _last_ step in the per-shadow-root context, not the first.

### Step 2 — Layer the per-shadow-root cascade

In `Base.ts`, every Lit element adopts four kinds of stylesheets in order: `PFBase`, component styles, `AKBase`, brand custom CSS. The shadow root is a self-contained cascade context, so we can move all four into layers in one PR without touching the document cascade:

- `PFBase` and `AKBase` get wrapped in `@layer components` at their CSS sources.
- Component styles get wrapped in `@layer components` by their authoring template.
- Brand custom CSS gets wrapped in `@layer overrides` by `createStyleSheetUnsafe` (or a new variant) before adoption.
- Each shadow root has a layer-order declaration at the top of the first adopted sheet.

After this step, brand custom CSS wins inside shadow roots without specificity duels. The document cascade is unchanged.

### Step 3 — Layer the document cascade

Wrap the per-file imports in `interface.global.css`, `flows.global.css`, and `static.global.css` into their target layers via `@import ... layer(...)`. Audit ordering against current behavior using visual regression on the Storybook before merging.

### Step 4 — Move user-facing `branding_custom_css` outside the shadow boundary, layered

Today brand custom CSS is per-shadow-root. Authors who want to target light-DOM elements (server-rendered flow pages, headers) cannot reach them. A future change could also inject branding CSS into the document head wrapped in `@layer overrides`. Out of scope for this RFC.

## Risks and how to detect them

- **Specificity inversion.** Moving a `.foo` rule into a layer demotes it relative to any unlayered `.foo`. Detection: visual regression against Storybook + flow executor stories before/after each step.
- **PatternFly internals depending on cascade order.** PF's own component CSS sometimes relies on order-of-import. Detection: confine layering to authentik-authored CSS first; PF stays unlayered until step 3.
- **Brand custom CSS that uses `!important`.** Some users have written `!important` overrides because they had no other recourse. Layering will still respect `!important`, so existing customizations should keep working, but they become unnecessary.

## What we want from this conversation

- Agree on the layer names and order in [Target cascade order](#target-cascade-order).
- Decide whether step 0 (reserve only) is worth landing now as a marker, or wait until step 2 is ready.
- Identify any shadow root that adopts stylesheets outside `Base.ts` and would be missed by step 2.
- Identify dashboards or stories that should sit in the visual-regression checklist for step 3.

## References

- [MDN cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer)
- [CSS Cascade Layers explainer](https://www.bram.us/2021/09/15/the-future-of-css-cascade-layers-css-at-layer/)
- [Open UI: layering](https://open-ui.org/)
