---
title: Cascade layers
sidebar_label: Cascade layers
description: How authentik's web UI orders its CSS with @layer, and where each kind of rule belongs.
---

authentik's document CSS is ordered with [cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer). Layers make the ordering explicit, so a rule's precedence comes from the layer it is assigned to rather than from where it happens to be imported or how specific its selector is.

## The layer order

One declaration, in `web/src/styles/layers.css`, defines the order for the whole document. It is the first import in every entrypoint:

```css
@layer reset, vendor, components, theme, mode, brand;
```

Lowest precedence first:

| Layer        | Holds                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------ |
| `reset`      | Top-level normalization. Sparse — most of the reset is folded into PatternFly.                   |
| `vendor`     | Vendored PatternFly and the bundled typefaces. Frozen; do not hand-edit.                         |
| `components` | Document-scope component rules, and the `:root` blocks bridging global tokens to component ones. |
| `theme`      | The default design tokens. CSS custom property definitions only.                                 |
| `mode`       | Light/dark, high-contrast, and reduced-motion overrides of `theme`.                              |
| `brand`      | Per-deployment branding overrides.                                                               |

`layers.css` is the only place the order is declared. Adding a layer anywhere else creates a second, independent ordering rather than extending this one.

## Assigning a rule to a layer

Layers are applied **only in the entrypoint files**, on the import itself:

```css
/* web/src/styles/interface.global.css */
@import "#styles/layers.css";

@import "#styles/global/vendor/patternfly.css" layer(vendor);
@import "@goauthentik/fonts/faces.css" layer(vendor);
@import "#styles/global/theme/variables.css" layer(theme);
@import "#styles/global/reset/globals.css" layer(reset);
@import "#styles/global/mode/mode.css" layer(mode);
@import "#styles/authentik/components/Placeholder/placeholder.css" layer(components);
```

The three entrypoints — `interface.global.css` (Admin and User), `flows.global.css` (Flow), and `static.global.css` (Django templates) — contain only `@import` statements. Individual stylesheets never wrap themselves in `@layer`, which keeps every precedence decision in one reviewable file per bundle.

Import order still matters _within_ a single layer. Across layers it does not: a later layer always wins, regardless of import order or selector specificity.

## Two cascade contexts

authentik has two independent cascades, and layers only govern the first.

**The document.** Driven by the three `.global.css` entrypoints, ordered by the layer stack above.

**Each shadow root.** Every component extending `AKElement` (`web/src/elements/Base.ts`) adopts, in order: `shadow/patternfly-base.css`, the component's own styles, `shadow/authentik-base.css`, and then brand custom CSS. These sheets are unlayered.

The bridge between the two is inheritance. CSS custom properties defined at the document level cross the shadow boundary, so a component reads `--ak-color-primary` without importing anything. What crosses is the _computed_ value — whichever declaration won at the document level.

This has a consequence worth internalizing:

> Layers order **selectors**, not properties.

Once a custom property crosses into a shadow root, the layer it was declared in no longer applies. Only its computed value carries over, and a declaration on `:host` inside the shadow root overrides what was inherited. Declare custom properties in consistent "dictionary" containers — `:root` at the document level, `:host` in shadow roots — so their specificity is predictable at the boundary.

## Brand customization

Brands customize appearance two ways, and they land in different places:

- **Custom properties from the database** are injected into the reserved `brand` layer, the last in the order, so they override theme and mode without needing `!important`.
- **A custom CSS file** is adopted per shadow root, after the component's own styles, so it can reach into `::part()` surfaces.

Because the custom CSS path is adopted last within its shadow root rather than being layered, existing `!important` declarations in brand CSS keep working. They are usually unnecessary.

## Adding CSS

- A new document-level component rule goes in `web/src/styles/authentik/components/<Name>/`, imported into the relevant entrypoint with `layer(components)`.
- Classes for light-DOM content — markup the document owns even when a component slots and positions it — are document-level component rules too, and go in `layer(components)` with the rest. If this category grows, it may earn a dedicated layer between `components` and `theme` so slotted-content styling can be reasoned about separately; today the volume does not justify extending the layer order.
- A new design token goes in `web/src/styles/global/theme/`, which is already imported into `layer(theme)`.
- A light/dark or accessibility override goes in `web/src/styles/global/mode/`.
- Anything vendored from PatternFly goes through `web/src/styles/global/vendor/patternfly.css`.

`web/src/styles/README.md` is the in-repo companion to this page, with the full directory layout and a "what is where" index.

## References

- [MDN: cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer)
- [MDN: using shadow DOM](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM)
