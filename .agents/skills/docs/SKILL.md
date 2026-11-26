---
name: docs
description: >
    Preview an authentik docs or integration-guide change locally with live reload, then
    run the same build, link and lint checks CI runs before you open a PR. Also maps each
    kind of content to the site that publishes it. Use when someone asks to "preview the docs",
    "start the docs server", "where does this page live", "the docs build fails on a broken
    link", "add an integration guide", or "check the docs before my PR". Writing style and
    site structure are in website/AGENTS.md. The product web UI belongs to frontend, spelling
    and lint tooling to linting, and PR conventions to contributing.
---

# authentik docs preview and checks

## Purpose

`website/` is a pnpm workspace that builds three separate Docusaurus sites. This skill gets
a change on screen quickly and through the checks that fail PRs. Site structure, authoring
rules, redirects and spelling policy live in [`website/AGENTS.md`](../../../website/AGENTS.md)
and the style guide at `website/docs/developer-docs/docs/style-guide.mdx`. Read those for
anything about content. This skill doesn't repeat them.

## Which site owns what

| Content                                     | Source                  | Published at                | Preview                   | Check before PR       |
| ------------------------------------------- | ----------------------- | --------------------------- | ------------------------- | --------------------- |
| Product docs, developer docs, release notes | `website/docs/`         | docs.goauthentik.io         | `make docs-watch`         | `make docs`           |
| Third-party integration guides              | `website/integrations/` | integrations.goauthentik.io | `make integrations-watch` | `make integrations`   |
| API reference (generated from `schema.yml`) | `website/api/`          | api.goauthentik.io          | `make docs-api-watch`     | `make docs-api-build` |

Never hand-edit API reference pages. Change the Python API, run `make gen`, then rebuild.

## When to invoke

- "Preview my docs change."
- "Where's the source for this page?"
- "The docs build fails with a broken link / anchor."
- "Run the docs checks before I push."

Not this skill: what to write and how (style guide), the web UI (frontend), cspell
dictionaries and lint config (linting).

## Workflow

Steps are tagged: `[shell]` run a command, `[edit]` change a file, `[verify]` check before
moving on. Run commands from the repo root. The package manager is **pnpm**.

### 1. Preview with live reload

1. **[shell]** Once, and after lockfile changes: `make docs-install` (runs `node-install`,
   which checks your Node and pnpm versions against `package.json`, then installs
   `website/`).
2. **[shell]** Start the site you're editing: `make docs-watch` or `make integrations-watch`.
   Docusaurus prints the local URL (port 3000 by default, or another port it offers if 3000
   is taken).
3. **[edit]** Save the `.mdx` file. The page reloads.
4. **[verify]** A new Topics page also needs an entry in `website/docs/sidebar.mjs` or it
   won't show in the navigation. Integration guides mustn't touch a sidebar. Theirs is
   generated from `website/integrations/categories.mjs`.

### 2. Check before opening a PR

1. **[shell]** `make docs` (spellcheck, oxlint, oxfmt, then a production build), or
   `make integrations` for integration guides. Both rewrite files. Commit what they change.
2. **[shell]** `make docs-check` reproduces CI's non-mutating lint job (`lint:check`,
   `build:types`, `format:check`).
3. **[verify]** The build passes. The shared config sets `onBrokenLinks`,
   `onBrokenAnchors`, `onDuplicateRoutes`, `onBrokenMarkdownLinks` and
   `onBrokenMarkdownImages` to `throw`, so the production build is the link check.
4. **[verify]** After pushing, review the PR's Netlify Deploy Preview.

## Gotchas

- **The dev server doesn't catch broken links.** Only the production build does. A page that
  looks fine in `docs-watch` can still fail CI. Run `make docs` before pushing.
- **`.md` pages fail the build.** All three sites accept only `.mdx`. Non-page partials may
  stay `.md` if their name starts with `_`.
- **A moved or renamed page breaks published URLs.** Add a rule to that site's
  `static/_redirects`. See "URLs and redirects" in `website/AGENTS.md`.
- **cspell runs in typo-only mode.** New product names need no dictionary entry. It flags
  only common misspellings and British spellings. Intentional ones go in
  `locale/en/dictionaries/overrides.txt`.
- **`make docs-build` stops early on a Node or pnpm mismatch** (`scripts/node/lint-runtime.ts`).
  Switch to the version in `package.json` `engines` rather than bypassing it.
- **The API site generates pages from `schema.yml`.** If the reference looks stale, rerun
  `make docs-api-watch` (it runs `generate` first) or `make docs-api-clean`.
- **The product name is always lowercase `authentik`**, even at the start of a sentence.
