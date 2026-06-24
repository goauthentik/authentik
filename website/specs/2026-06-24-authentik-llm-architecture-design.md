# authentik LLM-friendly docs + agent architecture

- **Status:** Design — pending implementation plan
- **Date:** 2026-06-24
- **Branch:** `llm-friendly-docs`
- **Spans repos:** `authentik` monorepo (`website/`) for Layer 1; `authentik-llm-marketplace` for Layers 2–3
- **Reviewed with:** DeepSeek (3-turn structural consult, session `019ef79b…`)

## Goal

Let AI coding agents (Claude Code, Cursor) reliably help authentik admins by
**preferring live retrieval over training data** — authentik changes
significantly between releases, so an agent's pretrained knowledge is routinely
stale. We achieve this with three layers, each fed by an artifact authentik
**regenerates every release**, so steady-state maintenance trends toward zero:

```
                 authentik (source of truth, regenerated per release)
                 ├── website MDX (docs + integrations) ─► Layer 1 (llms.txt + .md)
                 └── schema.yml (OpenAPI) ─► @goauthentik/api ─┐
                                                               ▼
   Agent ◄── Layer 2 (skills/rules: "prefer retrieval, start here") ─┘
     │
     └──────► Layer 3 (MCP server: observe + guarded act on a live instance)
```

Question routing:

- **Doc questions** ("How do I configure SAML?", "App vs Provider?") → L1 + L2, no instance.
- **Instance questions** ("show me the last 10 failed logins", "which version am I running?") → L3.
- **Hybrid / action questions** ("add a captcha to my login flow", "reset my admin password") → L2 reads docs to understand the concept, L3 acts.

## Non-goals (YAGNI)

- No master root `llms.txt` on a third domain (docs/integrations cross-link instead).
- No precomputed docs→API mapping registry in v1 (see "Deferred: tasks.json").
- No large hand-written tool surface in the MCP server (generic-first; curated tools are demand-driven).
- No adoption/fork of the community `authentik-mcp` (raw HTTP, ignores the generated client, 4× duplication, no guards — high per-release burden).

---

## Layer 1 — Docusaurus `llms.txt` plugin

Ported (leaner) from `docusaurus-plugin-llms` into the shared theme package.

### Location & packaging

New `docusaurus-theme/llms-txt/` directory, sibling to `releases/` and
`redirects/`, shipped as source (no build step), matching the existing pattern:

- `plugin.mjs` — Docusaurus plugin factory (default export)
- `node.mjs` — file discovery, MDX resolution, generation logic
- `common.mjs` — option/data types
- Add `"./llms-txt/plugin"`, `"./llms-txt/node"`, `"./llms-txt/common"` to `package.json` `exports`.

### Hook

`postBuild` — gives final resolved route URLs (`routesPaths`). This deviates
from the `loadContent`/`contentLoaded` pattern the theme's other plugins use,
and that is intentional: accurate final URLs require the post-build phase.

### Outputs (three-level "index of indexes")

Per the llmstxt.org convention, for **each** of the two sites (separate
subdomains `docs.goauthentik.io`, `integrations.goauthentik.io`):

1. **`/llms.txt`** — grouped root index. Opens with a cross-link header pointing
   at the sibling site's `/llms.txt`. Groups by topic (docs) / category
   (integrations, driven by the existing `categories.mjs`).
2. **`<dir>/llms.txt`** — per-topic / per-category index (e.g.
   `integrations.goauthentik.io/cloud-providers/llms.txt`,
   `docs.goauthentik.io/add-secure-apps/llms.txt`), indexing just that subtree,
   cross-linking up to the parent index.
3. **`/llms-full.txt`** — full concatenated content for the site. Retained
   (not redundant): it is the best single payload for RAG-index seeding and
   bulk/offline download. Cheap once the plugin already walks the site.
4. **Per-page `<page>.md`** — the **last-hop payload** (see below). Index links
   point at these `.md` files (the llmstxt.org `.md`-suffix convention).

### Per-page `.md` payload — core, not optional

This is the decisive correction from the design review: without per-page `.md`,
an agent traverses the full index chain and then has nothing bite-sized to
fetch — only the oversized `llms-full.txt` or rendered HTML. So per-page `.md`
emission is **core**.

authentik's MDX is not plain Markdown — it uses **partial imports**
(`import X from '_shared.mdx'`) and **custom remark directives** (`:::ak-version`,
enterprise/preview/support badges). A raw `.mdx` copy would leak unresolved
imports (a hard failure — content simply missing) and directive noise. So the
emit step must:

1. Obtain the **resolved MDX AST before React component injection**.
2. **Inline partial imports** (reuse the source plugin's `resolvePartialImports` approach).
3. **Strip custom directives** (drop `:::ak-*` / badge nodes; they are noise to an agent).
4. Strip frontmatter, then **serialize clean Markdown**.

JSX that remains is acceptable — modern LLMs parse it; information loss is the
real risk, not residual JSX. This is a one-time, build-stable investment.

### Wiring

A `createLlmsPlugin(options)` helper in `docusaurus-theme/config.js`, called from
both `docs/docusaurus.config.esm.mjs` and
`integrations/docusaurus.config.esm.mjs`. Integrations passes its category map;
docs passes topic config.

### Ported lean

- **Keep:** two core generators (index + full), route-based URL resolution, glob
  ignore, ordering, section/category grouping, partial-import resolution +
  directive stripping (per above), batch processing.
- **Drop:** blog inclusion, `pathTransformation` (route resolution covers it),
  `customLLMFiles`, `keepFrontMatter`, `addPaths`/`ignorePaths`.
- **Deps:** `gray-matter` + `minimatch` (theme already uses `fast-glob`).

---

## Layer 2 — Marketplace skills/rules (`authentik-llm-marketplace`)

Follows the mature `cloudflare-llm-marketplace` template. The manifest,
`.cursor-plugin`, and `output-styles` scaffolding already exist; we fill the
empty `skills/`, `rules/`, `commands/`.

**One plugin, multiple skills.** Skills are **pointers + method, never knowledge
dumps**, and every skill carries the "prefer retrieval over pre-training,
authentik changes between releases" directive.

- `ak-docs` — "start at `docs.goauthentik.io/llms.txt`, follow to the topic index, fetch the page `.md`."
- `ak-integrations` — same, rooted at `integrations.goauthentik.io/llms.txt` → category index.
- `ak-instance-ops` — when a question needs the live instance, use the Layer 3 MCP tools; for actions, read the relevant doc `.md` first, then call the guarded write.

**Fragility mitigation:** skills hard-code **only the stable root entry-point
URLs** (`/llms.txt`) and instruct the agent to **traverse links dynamically**.
They must stay abstract enough to survive topic/category reorganization — no
deep paths baked into skill prose.

A small `rules/*.mdc` set provides file-glob auto-triggering (e.g. on
`*.tf`/Terraform, or authentik blueprint YAML). The llms.txt URLs from Layer 1
**are** these skills' entry points — that is the L2↔L1 seam.

---

## Layer 3 — Live-instance MCP server (`authentik-llm-marketplace/mcp-servers/`)

A **thin, schema-driven Node stdio server** built on `@goauthentik/api`, run
locally by the admin (`npx`), authed with their instance URL + an authentik API
token via env. (This deployment model is the one the community `authentik-mcp`
validated; we keep the model, discard the implementation.) The token carries the
admin's own permissions; the server enforces nothing beyond the write guards.

### Tool tiers (generic-first)

1. **Generic schema-backed core (build first):**
   - `find_endpoint(query)` — search operations from `schema.yml`.
   - `describe_endpoint(operationId)` — **returns the full parameter/body schema.**
     Mandatory: without it, generic invoke is a trap (the agent guesses params or
     falls back to stale training data).
   - `invoke_endpoint(method, path, params)` — dispatches via the generated typed
     client. **Guarded:** mutations require an explicit confirm/dry-run step.
   - `health` / `version` — trivial read tools.
   - **Read-only mode flag** disables all mutations (the "diag" use case as one
     server, not a fork).
2. **Curated journey tools (demand-driven, added later):** ergonomic wrappers for
   frequent tasks (recent failed logins, list apps/providers/flows) — added
   **only where the generic loop repeatedly falls short**, not up front. Mine the
   community repo's tool list for candidates.

Because both tiers ride `@goauthentik/api` / `schema.yml`, an API change flows in
on the next client regen — no per-endpoint hand-patching.

### Deferred: `tasks.json` docs→API bridge

A `tasks:` frontmatter convention (extracted by L1 into a `tasks.json`) was
considered to map doc procedures → endpoint sequences. **Deferred**, because it
is fundamentally a *schema-quality + prose-clarity* problem, not a mapping
problem, and hand-maintained `tasks:` frontmatter reintroduces the per-release
sync tax we are escaping. Prove the loop with **runtime synthesis**
(`find_endpoint` + `describe_endpoint` + clear prose + good OpenAPI operation
summaries). Add a minimal `tasks.json` **only** at the specific spots the MVP
shows failing.

**Kill criterion:** if the captcha MVP completes the loop via
`find_endpoint`/`describe_endpoint`/`invoke_endpoint` without a precomputed map,
`tasks.json` is superfluous — do not build it. If it fails, diagnose whether the
gap is a missing OpenAPI **operation summary** or ambiguous **doc prose**, and
fix *that* first; only patch with a minimal `tasks.json` as a last resort.

---

## The pivot test: "add a captcha to my login flow"

This single hybrid task exercises the entire L1→L2→L3 loop and is the gate that
validates the architecture before broad build-out. MVP can stub the live
authentik server (mock responses) and run L3 against a small schema slice
(get flow, get stage bindings, create captcha stage, bind stage).

---

## Build sequencing (dependency-ordered)

1. **L1 — core indexes + full-text.** `postBuild` plugin generating `/llms.txt`,
   `<topic>/llms.txt`, `/llms-full.txt` for the docs site. _Critical path._
2. **🛑 GATE — index sanity.** On a real docs snapshot: every link resolves,
   groupings correct, full-text contains content.
3. **L1 — per-page `.md`** with partial resolution + directive stripping; point
   all index links at the `.md` files. _Critical path._
4. **🛑 GATE — content quality.** 5 varied pages: no leftover imports, no badge
   cruft, readable Markdown; feed one to an LLM and confirm it can list the steps.
5. **L2 — `ak-docs` skill skeleton.** Entry-point URLs + traverse-and-fetch
   method. _Parallelizable_ once gate 2 fixes the entry-point URLs.
6. **L3 — MCP server core:** `find_endpoint` + `describe_endpoint` +
   guarded `invoke_endpoint` + read-only flag + health/version. _Parallelizable
   with L2; depends only on `schema.yml`. On the critical path for the pivot test._
7. **🛑 GATE — captcha MVP end-to-end (the pivot).** Agent follows L2 → reads
   captcha doc `.md` → discovers + invokes endpoints (mock server OK). On
   failure, diagnose schema/prose before considering `tasks.json`.
8. **L1 — integrations subdomain.** Run across both sites; cross-links.
9. **L2 — `ak-integrations`, `ak-instance-ops`, file-glob rules.** _Parallelizable_ once index structure stabilizes.
10. **L3 — curated journey tools.** _Only_ when the generic loop repeatedly falls short for frequent tasks.

---

## Cross-cutting

- **Distribution:** Claude Code + Cursor manifests already scaffolded; one skill set serves both.
- **Security:** local stdio keeps the admin's token in their own environment;
  writes gated behind confirm/dry-run; read-only mode available.
- **Maintenance thesis:** docs (`.md` + indexes) and API surface
  (`@goauthentik/api` from `schema.yml`) both regenerate from authentik each
  release; L2 is thin glue. Steady-state human upkeep approaches zero.

## Open questions for plan stage

- Exact `createLlmsPlugin` option surface and how docs vs. integrations configs differ.
- Mechanism to obtain the resolved-but-pre-React MDX AST within `postBuild` (Docusaurus internals vs. re-parsing source).
- MCP server package layout within the `mcp-servers/` workspace and how `schema.yml` is vendored/fetched at runtime.
- Whether `invoke_endpoint`'s guard is interactive confirm vs. a two-call dry-run/commit protocol.
