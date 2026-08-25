# The authentik docs sites

`website/` is a pnpm workspace that builds three separate Docusaurus sites, each its own package with its own `docusaurus.config.esm.mjs`, sidebar, and `static/_redirects`:

- `docs/` → [docs.goauthentik.io](https://docs.goauthentik.io), how to use and configure authentik.
- `integrations/` → [integrations.goauthentik.io](https://integrations.goauthentik.io), per-service SSO setup guides.
- `api/` → [api.goauthentik.io](https://api.goauthentik.io), generated from `../schema.yml`. Never hand-edit its reference pages.

The shared `docusaurus-theme/` package holds the theme code all three consume, including swizzled overrides of Docusaurus internals. Prefer wrapping over ejecting, and re-check overrides on a Docusaurus upgrade, because they shadow theme components that upgrades are allowed to change. Scaffold a new one with `docusaurus swizzle @docusaurus/theme-classic <Component> --wrap`, then move it into `docusaurus-theme/theme/` so all three sites share it.

Most work here is MDX content, not application code. A page's URL is a promise to readers, and the prose has to pass the linters.

## Commands

Run everything from the repo root through `make`. The targets wrap `pnpm --dir website` with the right ordering (this is a pnpm workspace; older references to npm and corepack are stale). `make docs` and `make integrations` are lint-fix plus a full build, and CI runs the same, so run the one matching your change before pushing. `make docs-watch` and `make integrations-watch` give a live dev server, and `make docs-install` repairs the tooling after dependency changes or odd build failures.

## Content is `.mdx` only

All three sites dropped `.md`. Create new pages as `.mdx`, and rename with `git mv <file>.md <file>.mdx` plus a `_redirects` entry if the page was already published. Files that are not pages (notes, partials) stay out of the build by an `_` prefix, which Docusaurus already excludes.

## Authoring

**`docs/developer-docs/docs/style-guide.mdx` is the source of truth. Read it before writing prose.** It covers terminology, voice, headings, frontmatter, callouts, and formatting; this file deliberately restates none of it, because a partial copy would drift. Page templates live in `docs/developer-docs/docs/templates/`, and `writing-documentation.mdx` next to the style guide covers routing, redirects, and the glossary field reference.

The rule no linter catches: the product name is always lowercase `authentik`, even at the start of a sentence. The company is Authentik Security, Inc., and Admin is capitalized only when naming the Admin interface.

The two sites navigate differently, and mixing this up is the most common structural mistake:

- A new Topics page must be added to `docs/sidebar.mjs` by hand or it silently doesn't appear.
- The integrations sidebar is generated from `integrations/categories.mjs`. Never edit it. A new guide starts as a copy of `integrations/template/service.mdx` into `integrations/<category>/<service>/index.mdx`, using the placeholder domains `authentik.company` and `<app-name>.company` (drop the service domain for SaaS).

Glossary terms are pages too: `docs/core/glossary/terms/<term>.mdx`, driven by `sidebar_custom_props` frontmatter (`termName`, `tags`, optional `shortDescription`). The field reference is in `writing-documentation.mdx`.

## URLs and redirects

File path → URL: strip the `website/<site>` prefix and the extension, add a trailing slash. Moving or renaming a page requires a rule in that site's `static/_redirects` (`/old/path  /new/path  301!`). Better organization rarely justifies breaking bookmarks, so don't move pages without a reason.

## Spell check

cspell runs in typo-only mode. It flags known misspellings and British spellings, and lets unknown words pass silently, so a new integration or product name needs no dictionary entry. An intentional flagged spelling goes in `locale/en/dictionaries/overrides.txt` if it recurs, or a tightly scoped `<!-- spellchecker:ignore word -->` for a one-off. Never disable the checker for a whole page.

## Deployment

Netlify builds every PR into a Deploy Preview. Check rendering and links there before requesting review. `docs.goauthentik.io` tracks the current release, `main.goauthentik.io` tracks `main`, and `version-YYYY-MM.goauthentik.io` pins a release.
