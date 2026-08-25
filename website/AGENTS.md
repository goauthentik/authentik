# website/ — the docs sites

A pnpm workspace building three separate Docusaurus sites, each its own package with its own `docusaurus.config.esm.mjs`, sidebar, and `static/_redirects`:

- `docs/` → [docs.goauthentik.io](https://docs.goauthentik.io) — how to use and configure authentik
- `integrations/` → [integrations.goauthentik.io](https://integrations.goauthentik.io) — per-service SSO setup guides
- `api/` → [api.goauthentik.io](https://api.goauthentik.io) — GENERATED from `../schema.yml`, never hand-edit its reference pages

`docusaurus-theme/` is the shared theme package, including swizzled overrides of Docusaurus internals. Prefer wrapping over ejecting, re-check overrides on Docusaurus upgrades. Scaffold with `docusaurus swizzle @docusaurus/theme-classic <Component> --wrap`, then move the result into `docusaurus-theme/theme/` so all three sites share it.

## Commands

Run from the repo root. The make targets wrap `pnpm --dir website` (this is a pnpm workspace — older references to npm/corepack are stale).

```bash
make docs                # lint-fix + build the Topics site — run before pushing, CI runs the same
make integrations        # lint-fix + build the integrations site
make docs-watch          # live dev server (integrations-watch for the other site)
make docs-install        # (re)install tooling after dependency changes or odd build failures
make lint-spellcheck     # cspell (also part of docs-lint-fix)
```

## Content rules

- **`.mdx` only.** All three sites dropped `.md`. Rename with `git mv <file>.md <file>.mdx` plus a `_redirects` entry if the page was published. Non-page files (notes, partials) stay out of the build via an `_` prefix.
- **`docs/developer-docs/docs/style-guide.mdx` is the source of truth for prose** — terminology, voice, headings, frontmatter, callouts, formatting. Read it before authoring; this file deliberately restates none of it. Page templates: `docs/developer-docs/docs/templates/`. Routing, redirects, and the glossary field reference: `writing-documentation.mdx` next to the style guide.
- The rule no linter catches: the product name is always lowercase `authentik`, even at the start of a sentence. The company is Authentik Security, Inc. "Admin" is capitalized only when naming the Admin interface.

## Adding pages

- **Topics page**: create the `.mdx` under `docs/<area>/`, add it to `docs/sidebar.mjs` by hand (or it silently doesn't appear), run `make docs`.
- **Integration guide**: copy `integrations/template/service.mdx` to `integrations/<category>/<service>/index.mdx` (category from `integrations/categories.mjs`). Placeholder domains: `authentik.company` and `<app-name>.company` (drop the service domain for SaaS). The integrations sidebar is generated from `categories.mjs` — never edit it. Run `make integrations`.
- **Glossary term**: `docs/core/glossary/terms/<term>.mdx` with `sidebar_custom_props` frontmatter (`termName`, `tags`, optional `shortDescription`).

## URLs and redirects

- File path → URL: strip the `website/<site>` prefix and the extension, add a trailing slash.
- Moving or renaming a page requires a rule in that site's `static/_redirects`: `/old/path  /new/path  301!`. Don't move pages without a reason — better organization rarely justifies breaking bookmarks.

## Spell check

cspell runs in typo-only mode: it flags known misspellings and British spellings, and unknown words (product names, jargon) pass silently — a new integration needs no dictionary entry. For an intentional flagged spelling: `locale/en/dictionaries/overrides.txt` if it recurs, or a tightly scoped `<!-- spellchecker:ignore word -->` for a one-off. Never disable the checker for a whole page.

## Deployment

Netlify + GitHub Actions. Every PR gets a Deploy Preview — check rendering and links there before requesting review.

| Subdomain                        | Tracks          |
| -------------------------------- | --------------- |
| `docs.goauthentik.io`            | current release |
| `main.goauthentik.io`            | `main`          |
| `next.goauthentik.io`            | `next`          |
| `version-YYYY-MM.goauthentik.io` | a release       |
