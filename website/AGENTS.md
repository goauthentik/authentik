## Project Overview

This is the **authentik documentation website** — the source for everything published under `goauthentik.io`. It is a TypeScript [NPM Workspace](https://docs.npmjs.com/cli/v11/using-npm/workspaces) at `./website` that builds **three separate [Docusaurus](https://docusaurus.io/) sites**, each its own workspace package with its own `docusaurus.config.esm.mjs`, `sidebar.mjs`, and `static/_redirects`:

- **Topics / "The Docs"** (`docs/`, pkg `@goauthentik/docs-topics`) → [docs.goauthentik.io](https://docs.goauthentik.io) — how to use authentik.
- **Integrations** (`integrations/`, pkg `@goauthentik/integration-docs`) → [integrations.goauthentik.io](https://integrations.goauthentik.io) — guides for using authentik with third-party services.
- **API** (`api/`, pkg `@goauthentik/api-docs`) → [api.goauthentik.io](https://api.goauthentik.io) — **generated** from the OpenAPI schema (`../schema.yml`); do not hand-edit reference pages.

A shared `docusaurus-theme/` workspace package (`@goauthentik/docusaurus-theme`) holds common theme, redirect, and component code consumed by all three. Common dependencies (Docusaurus, React, MDX) are hoisted to the root `node_modules`.

You are most often editing **Markdown/MDX content**, not application code. Treat documentation as a product: every page has a URL that is a promise to readers, and prose must pass the linters and the spell checker.

## Commands

All build/lint commands are driven from the **repo-root `Makefile`**, not from inside `website/`. Each target proxies to an NPM script via `corepack npm run --prefix website ...`. Run them from the repository root.

### Setup

```bash
make docs-install      # Install/update all docs build tooling (run first, and after build failures)
```

`make install` (the full dev environment) is a superset and also installs docs tooling.

### Topics docs (`docs/`)

```bash
make docs              # lint-fix + build — ALWAYS run before pushing a PR (CI fails otherwise)
make docs-watch        # Live dev server with hot reload
```

### Integration guides (`integrations/`)

```bash
make integrations        # lint-fix + build — run before pushing a PR
make integrations-watch  # Live dev server with hot reload
```

### API docs (`api/`)

```bash
make docs-api-watch    # Regenerate from schema + dev server
make docs-api-build    # Build generated API reference
make docs-api-clean    # Remove generated API reference
```

### Linting & spell check

```bash
make lint-spellcheck   # cspell over the repo (also part of docs-lint-fix)
make docs-lint-fix     # spellcheck + prettier --write
```

Inside `website/` the underlying scripts are `npm run prettier`, `npm run lint` / `npm run lint-check` (ESLint), and `npm run check-types` (`tsc -b`). Prefer the `make` targets — they wire up the correct working directory and ordering.

## Architecture

### Directory structure

```
website/
  docs/                 # Topics site (@goauthentik/docs-topics)
    add-secure-apps/    # Applications, providers, flows, stages, etc.
    core/               # Core concepts + glossary (core/glossary/terms/)
    customize/          # Branding, blueprints, policies, theming
    developer-docs/     # CONTRIBUTOR GUIDES — read these before authoring (see below)
    enterprise/ install-config/ releases/ security/ sys-mgmt/
    troubleshooting/ users-sources/ expressions/ endpoint-devices/
    sidebar.mjs         # Hand-maintained nav for the Topics site
    static/_redirects   # Netlify redirect rules for moved/renamed pages
  integrations/         # Integrations site (@goauthentik/integration-docs)
    <category>/<service>/index.mdx   # one folder per service
    categories.mjs      # Category list — drives the AUTO-GENERATED sidebar
    template/service.md # Template for a new integration guide
    static/_redirects
  api/                  # API site (@goauthentik/api-docs) — generated from ../schema.yml
  docusaurus-theme/     # Shared theme/components/redirect logic for all three sites
  scripts/              # Build/lint helper scripts (e.g. lint-runtime.mjs)
  static/               # Shared static assets
  package.json          # Root workspace definition
```

### Author-facing guides (source of truth — keep content consistent with these)

- `docs/developer-docs/docs/writing-documentation.md` — setup, build commands, glossary, page routing & redirects.
- `docs/developer-docs/docs/style-guide.mdx` — the canonical style guide (terminology, voice, formatting, accessibility, metadata).
- `docs/developer-docs/docs/templates/` — `combo` / `procedural` / `conceptual` / `reference` templates (`*.tmpl.md`). Start from a template; default to **combo** unless the steps get buried, then split into procedural + conceptual.
- `docs/developer-docs/contributing.md` — general contribution guidelines.

When you change a documented workflow (commands, structure, conventions), update both this file **and** the corresponding author-facing guide so they don't drift.

## Authoring conventions

These mirror `style-guide.mdx`; consult it for the full set.

- **Product name is always `authentik`** — lowercase `a`, never capitalized, even at the start of a sentence. The company is **Authentik Security, Inc.**. Capitalize **Admin** only when naming the Admin interface.
- **Sentence case** for titles and headings ("Configure the Google Workspace provider", not Title Case).
- **American English**, active voice, present tense, Oxford comma.
- **Frontmatter**: every page needs `title`. Common fields: `sidebar_label`, `description`, `support_level` (integrations: `community` for community-maintained, `authentik` for team-tested, `deprecated`), and authentik directives (`:ak-version[...]`, `:ak-preview`, `:ak-enterprise`).
- **Callouts**: `:::info` (with optional title), `:::warning`, `:::danger` for irreversible actions.
- **Formatting**: **bold** for UI elements/actions, `code` for commands/paths/inline code, `<angle_brackets>` (underscores for spaces) for placeholders.
- **Code blocks**: always set a language; `title="path"`, `showLineNumbers`, and `{n}` line highlighting are available.
- **Accessibility**: descriptive alt text and link text, no skipped heading levels, gender-neutral pronouns, avoid idioms/ableist terms.
- **Images sparingly** — prefer Mermaid diagrams (version-controllable) over screenshots.

### Adding a Topics page

1. Create the `.md`/`.mdx` file under the appropriate `docs/<area>/` directory.
2. **Add it to `docs/sidebar.mjs`** — otherwise it won't appear in the navigation.
3. Run `make docs` before pushing.

### Adding an integration guide

1. Copy `integrations/template/service.md` into `integrations/<category>/<service>/index.mdx`. Pick a `<category>` from `integrations/categories.mjs`.
2. Use placeholder domains `authentik.company` and `<app-name>.company` (drop the service domain for SaaS).
3. **Do not edit the integrations sidebar** — it is auto-generated from `categories.mjs`.
4. Run `make integrations` before pushing.

### Adding a glossary term

Create `docs/core/glossary/terms/<term>.mdx` with `sidebar_custom_props` frontmatter (`termName`, `tags`, optional `authentikSpecific`, `shortDescription`, optional `longDescription`). See `writing-documentation.md` for the field reference.

## URLs and redirects

File path → URL: drop the `website/<site>` prefix, strip the extension, add a trailing slash (e.g. `website/docs/developer-docs/docs/style-guide.mdx` → `https://docs.goauthentik.io/developer-docs/docs/style-guide/`).

**Every URL is a promise — `_redirects` exist so links never break.** When you move or rename a page:

1. Move the file and update its `sidebar.mjs` entry.
2. Add a rule to the site's `static/_redirects` (`/old/path  /new/path  301!`).

Avoid renaming/moving pages unless necessary; better organization rarely justifies breaking bookmarks.

## Spell checking

Spell checking uses **cspell** (`make lint-spellcheck`, config `../cspell.config.jsonc`). Custom dictionaries live in `../locale/en/dictionaries/` (`software-terms.txt`, `integrations.txt`, `idp.txt`, language-specific lists, `people.txt`, `ignore.txt`). Add genuinely new product/service/technology terms to the appropriate dictionary rather than rewording correct prose; never disable the checker for a page.

## Deployment

Deployment is handled by Netlify plus GitHub Actions. Branches map to subdomains:

| Subdomain                        | Branch           |
| -------------------------------- | ---------------- |
| `docs.goauthentik.io`            | current release  |
| `main.goauthentik.io`            | `main`           |
| `next.goauthentik.io`            | `next`           |
| `version-YYYY-MM.goauthentik.io` | specific release |

Every PR gets a Netlify Deploy Preview — use it to verify rendering, links, and any Docusaurus-specific features before requesting review.

## Tech Stack

| Concern        | Tooling                                                                             |
| -------------- | ----------------------------------------------------------------------------------- |
| Site generator | Docusaurus 3.x (classic preset + Mermaid)                                           |
| Content        | Markdown / MDX + React                                                              |
| API reference  | `docusaurus-plugin-openapi-docs` (from schema)                                      |
| Build runtime  | Node ≥ 24, npm ≥ 11 (run via `corepack`)                                            |
| Package layout | NPM Workspaces (`docs`, `integrations`, `api`, `docusaurus-theme`)                  |
| Lint / format  | ESLint 9 (`@goauthentik/eslint-config`) + Prettier (`@goauthentik/prettier-config`) |
| Spell check    | cspell + shared dictionaries                                                        |
| Types          | TypeScript (`tsc -b`)                                                               |
| Hosting        | Netlify + GitHub Actions                                                            |
