# Theme font-token consolidation + Docusaurus alignment

**Date:** 2026-06-23
**Status:** Approved design
**Scope:** `packages/theme`, `web/src/styles/authentik/base/fonts.css`, `packages/docusaurus-config`

## Problem

The RedHat font stack and the brand primary color are defined independently in
three places:

- **Web app** (`web/src/styles/authentik/base/fonts.css`) — the `--ak-generic-*`
  and `--ak-font-family-*` layers, with concrete RedHat stacks.
- **Docs** (`packages/docusaurus-config/css/fonts.css` + `root.css`) — its own
  `@font-face` set and hardcoded `--ifm-font-family-*` / `--ifm-color-primary`.
- **Theme** (`packages/theme/lib/tokens/typography.js`) — semantic font tokens
  (`font.family-body/heading/code`) that are currently **unresolved aliases**
  pointing at `--ak-font-family-sans-serif` / `--ak-generic-display` /
  `--ak-font-family-monospace`, which only the web app defines.

The two surfaces already use the **same RedHat variable font files**; they only
disagree on the `@font-face` family name (`"RedHatText"` vs `"RedHatTextVF"`) and
the `src` URL (web bundles from `./`; docs loads from `goauthentik.io`). The docs
`--ifm-color-primary: #fd4b2d` is exactly the theme's `color.accent`
(`rgb(253, 75, 45)`).

## Goals

1. Make `@goauthentik/theme` the single source of truth for font **tokens** and
   the brand **primary**, so the web app and the docs align without duplicated
   stacks.
2. Keep `@font-face` and font **files** per-consumer — their `src` URLs are
   genuinely environment-specific.
3. Add no unnecessary heft to the Docusaurus CSS: the docs consume only the
   token categories they use.

## Non-goals

- Moving font files or `@font-face` into the theme package (rejected: forces one
  hosting strategy on both surfaces).
- Generating tint/shade ramps for the 6 Infima primary shades. Noted as a future
  follow-up (an OKLCH-derived ramp — Ken's review point #1 — could replace the
  hand-tuned hex). For now the docs keep their existing shades.
- Moving the CJK locale font overrides out of the web app. They stay in
  `web/src/styles/locales/*/globals.css` and remain the per-language override
  seam; we will build on them in the near future.

## Design

### Principle

Canonical font-family names are the web app's existing ones: `"RedHatText"`,
`"RedHatDisplay"`, `"RedHatMono"`. The theme references these names in concrete
token stacks. Each consumer registers `@font-face` for the same names with its
own `src`.

Token layering (defaults owned by the theme):

```
--ak-generic-*           (concrete stacks: "RedHatText", sans-serif, ...)
  ↓ var()
--ak-font-family-*       (alias/override layer: sans-serif, heading, monospace)
  ↓ var()
--ak-font-family-body/heading/code   (semantic typography tokens)
```

The middle `--ak-font-family-*` layer is the override seam the CJK locale globals
redefine via `html[lang="ja"]` selectors. Because those selectors outrank
`:root`, the locale overrides keep winning regardless of where the defaults are
declared.

### Theme package (`packages/theme`)

- **New token module `lib/tokens/font-family.js`** registering the full layer,
  with the web app's current values verbatim:
  - `--ak-generic-serif`, `--ak-generic-sans-serif`, `--ak-generic-monospace`,
    `--ak-generic-symbols`, `--ak-generic-emoji`, `--ak-generic-body`,
    `--ak-generic-heading`, `--ak-generic-display`.
  - `--ak-font-family-sans-serif`, `--ak-font-family-heading`,
    `--ak-font-family-monospace`.
- Register the new module in `lib/tokens/index.js` (before `typography.js` so the
  generic/family layer is declared ahead of the semantic tokens that reference
  it; styleframe emits in registration order).
- `typography.js` semantic tokens are unchanged in intent but now resolve
  in-package.
- **Resolve the `--ak-font-family-heading` collision.** It is currently defined
  twice — `var(--ak-generic-heading)` (web `base/fonts.css`) and
  `var(--ak-generic-display)` (theme `typography.js` `font.family-heading`).
  Implementation step: determine which value currently renders (by cascade order
  in the built web app) and preserve that behavior in the single consolidated
  definition. If the two are found to disagree in practice (one is a latent bug),
  flag it and pick the value matching the PF heading mapping
  (`--pf-global--FontFamily--heading--sans-serif: var(--ak-generic-display)`)
  rather than silently changing rendered output.
- **Add the `generic-` prefix to the `typography` category in `scripts/build.mjs`.**
  The new generic tokens are named `--ak-generic-*`, which matches none of the
  existing category prefixes — without this they would appear only in
  `index.css`, leaving `dist/typography.css` with dangling `var(--ak-generic-*)`
  references and breaking the docs cherry-pick. With `generic-` added, the full
  font layer (generic stacks → family aliases → semantic tokens) lands in
  `typography.css` and is self-contained.
- New tokens otherwise flow through the existing build → dtcg → format pipeline
  unchanged, and into the self-contained `dist/index.css`.

### Web app (`web/src/styles/authentik/base/fonts.css`)

- Remove the `Generic Families` and `Font Families` regions (now inherited from
  the theme via the already-imported `@goauthentik/theme/index.css`).
- Keep the `PF Mapping` region (references `--ak-generic-*` / `--ak-font-family-*`,
  now theme-sourced) and the `Font Sizes and Weights` region.
- Keep `@import "#fonts/RedHat/faces.css"` (the `@font-face`) unchanged.
- Confirm the theme tokens are imported before `base/fonts.css` and the locale
  globals so the PF mappings resolve. `base/variables.css` already imports
  `@goauthentik/theme/index.css`; verify import order in `*.global.css`.

### Docs (`packages/docusaurus-config`)

- Add `@goauthentik/theme` as a dependency.
- **Import only the categories the docs use** — `@goauthentik/theme/color.css`
  and `@goauthentik/theme/typography.css` — at the top of `css/index.css`, NOT
  the whole `index.css`. (~2.2KB vs ~3.7KB; avoids pulling spacing/shadow/motion/
  z-index tokens the docs never reference. This is the use case the per-category
  split exists for.)
- `css/fonts.css`:
  - Rename the `@font-face` family names `"RedHatDisplayVF"`/`"RedHatTextVF"`/
    `"RedHatMonoVF"` → `"RedHatDisplay"`/`"RedHatText"`/`"RedHatMono"`. Keep the
    existing CDN `src` URLs and font files.
  - Replace the hardcoded `--ifm-font-family-base` / `--ifm-font-family-monospace`
    / `--ifm-heading-font-family` with bridges: `var(--ak-font-family-body)`,
    `var(--ak-font-family-code)`, `var(--ak-generic-display)`. This also fixes the
    currently-unregistered `RedHatVF` reference.
- `css/root.css`:
  - Bridge `--ifm-color-primary: var(--ak-color-accent)`.
  - Keep the 6 `--ifm-color-primary-{dark,darker,darkest,light,lighter,lightest}`
    hex values as-is (future: OKLCH-derived ramp).

## Verification

- `npm run build:assets` in the theme emits the new font tokens; dtcg token count
  increases; `dist/index.css` stays self-contained (no `@import`).
- `dist/typography.css` is self-contained: every `var(--ak-generic-*)` it
  references is also defined in the same file (the `generic-` category fix). The
  docs cherry-pick of `color.css` + `typography.css` resolves with no dangling
  vars.
- Web app: built CSS renders identical fonts (same family names, same files); no
  visual change. Grep confirms `base/fonts.css` no longer defines the generic or
  family layers.
- Docs: `--ifm-*` font and primary values resolve through `var(--ak-*)`. Grep
  confirms `css/fonts.css` no longer hardcodes the family stacks (only
  `@font-face` remains) and `root.css` no longer hardcodes the primary base.
- Lint/prettier clean across all three packages.

## Risks

- **`--ak-font-family-heading` behavior change.** Mitigated by preserving the
  currently-rendered value (see Theme step). Verify the web app heading font is
  unchanged before/after.
- **Import order.** If the theme tokens load after a consumer that references
  them, vars resolve to nothing. Mitigated by verifying order in the web
  `*.global.css` and the docs `css/index.css`.
- **Docs font-file parity.** The docs `src` points at `…Modified-updated.woff2`
  files on the CDN; renaming only the `@font-face` family (not the `src`) keeps
  those files in use. No font rendering change expected.
- **Package-specifier `@import` in Docusaurus.** `@import "@goauthentik/theme/
  color.css"` from inside `css/index.css` must resolve through Docusaurus's
  css-loader. Verify during implementation; if bare specifiers don't resolve in
  this `@import` context, fall back to referencing the files through the package
  `exports` the way the existing docs CSS is wired, or load them as additional
  theme stylesheets.
