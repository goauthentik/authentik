# authentik agent-friendly docs + agent architecture

- **Status:** Design — Layer 1 shipped (PR #23360); Layer 3 redesigned around code-mode
- **Date:** 2026-06-24
- **Revised:** 2026-06-24 — Layer 3 reworked from a tool-per-endpoint MCP to **code-mode** (see "Reviewed with").
- **Branch:** `agent-friendly-docs`
- **Spans repos:** `authentik` monorepo (`website/`) for Layer 1; `authentik-agent-marketplace` for Layers 2–3
- **Reviewed with:** DeepSeek (3-turn structural consult, session `019ef79b…`); the code-mode literature — Cloudflare [code-mode](https://blog.cloudflare.com/code-mode/), [code-mode-mcp](https://blog.cloudflare.com/code-mode-mcp/), [enterprise-mcp](https://blog.cloudflare.com/enterprise-mcp/), and Ronacher [_MCPs need code, not 30 tools_](https://lucumr.pocoo.org/2025/8/18/code-mcps/).

## Goal

Let AI coding agents (Claude Code, Cursor) reliably help authentik admins by
**preferring live retrieval over training data** — authentik changes
significantly between releases, so an agent's pretrained knowledge is routinely
stale. We achieve this with three layers, each fed by an artifact authentik
**regenerates every release**, so steady-state maintenance trends toward zero:

```
                 authentik (source of truth, regenerated per release)
                 ├── website MDX (docs + integrations) ─► Layer 1 (llms.txt + .md)
                 └── /api/v3/schema/ (OpenAPI) ──────────► Layer 3 search()
                                                               │
   Agent ◄── Layer 2 (skills: "learn from docs, then write code") ┘
     │
     └──────► Layer 3 (code-mode MCP: search the spec, write `ak.request(...)`
                        in a sandbox to observe / guarded-act on a live instance)
```

Both retrieval surfaces follow the same shape: hand the agent a cheap **index**
(docs `llms.txt`; API `schema.yml`) and let it **fetch/execute on demand**
rather than front-loading content or tools into context.

Question routing:

- **Doc questions** ("How do I configure SAML?", "App vs Provider?") → L1 + L2, no instance.
- **Instance questions** ("show me the last 10 failed logins", "which version am I running?") → L3.
- **Hybrid / action questions** ("add a captcha to my login flow", "reset my admin password") → L2 reads docs to understand the concept, L3 writes code to act.

## Non-goals (YAGNI)

- No master root `llms.txt` on a third domain (docs/integrations cross-link instead).
- No precomputed docs→API mapping registry (code-mode's `search` over the live spec subsumes it — see Layer 3).
- **No tool-per-endpoint MCP.** authentik's API is hundreds of endpoints; exposing each as a tool floods context and rots every release. Code-mode keeps a fixed ~3-tool surface regardless of API size.
- No adoption/fork of the community `authentik-mcp` (raw HTTP, hand-written tool-per-endpoint, 4× duplication, no guards — high per-release burden, and the wrong shape).

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

## Layer 2 — Marketplace skills (`authentik-agent-marketplace`)

Already built: **two role-split plugins** under `plugins/`, each a set of
skills that are **pointers + method, never knowledge dumps**:

- **`ak-admin`** (12 skills) — organized by authentik's object model: `concepts`,
  `applications`, `providers`, `sources`, `flows-stages`, `authenticators-mfa`,
  `policies-rbac`, `users-directory`, `outposts`, `events-monitoring`,
  `troubleshooting`, `operations`.
- **`ak-dev`** (11 skills) — contributing to authentik: dev-environment, backend,
  frontend, docs, testing, linting, contributing, community, de-slop.

Each skill is `name` + `description` + Purpose + "When to invoke" + "Not this
skill". Every skill carries the "prefer retrieval over pre-training, authentik
changes between releases" directive.

**The two seams (near-term wiring, tracked separately from this redesign):**

- **L2 → L1 (docs):** each skill points at the stable root entry-point URL only
  (`docs.goauthentik.io/llms.txt` or `integrations.goauthentik.io/llms.txt`) and
  tells the agent to **traverse links dynamically** and fetch the page `.md`. No
  deep paths baked into skill prose (survives doc reorganization). The `llms.txt`
  URLs from Layer 1 **are** these skills' entry points.
- **L2 → L3 (instance):** the `ak-admin` skills add one steering line — *"to
  inspect or change the live instance, use the code-mode MCP: `search` for the
  endpoint, then write `ak.request(...)` in `execute` / `execute_write`. Learn the
  concept from the docs first."* `events-monitoring` → `execute`; `flows-stages`,
  `users-directory`, etc. → `execute_write`.

This single pair of seams is what ties the three layers: docs teach the concept,
code-mode acts. (The `.mcp.json` registration and a `SessionStart` deps-install
hook are already scaffolded in the repo for the Layer 3 server.)

---

## Layer 3 — Code-mode MCP server (`authentik-agent-marketplace/mcp-servers/`)

Instead of exposing authentik's API as N tools, expose its **OpenAPI spec for
search and a sandbox for code**, and let the agent write code against an
authenticated `ak.request(...)` helper. This is the code-mode pattern (Cloudflare,
Ronacher): LLMs are far better at writing code than at emitting tool calls, and a
code surface collapses a hundreds-of-endpoints API to a fixed ~3-tool, near-fixed
token footprint that **does not grow as the API grows** and tracks the running
instance's version for free.

### The three tools (shared by v1 and v2)

- **`search(query)`** — query the resolved `schema.yml` (all `$ref`s inlined) and
  return only the matching operations: `method + path + summary + param / request /
  response schema slices`. This is the only output that scales with the API, and
  it returns slices, never the whole spec. (Replaces the prior
  `find_endpoint`/`describe_endpoint` pair — search returns the param/response
  schema the agent needs to construct a call.)
- **`execute(code)`** — run the agent's JS/TS in a sandbox whose only capability is
  a bound **`ak.request(method, path, { query, body })`** helper. **Read-only:**
  rejects any non-GET verb.
- **`execute_write(code)`** — same sandbox, **full** `ak.request` (all verbs).
  **Requires per-call confirmation.** Because it carries reads too, a mixed
  find→create→bind chain runs as one confirmed block — code-mode's composability is
  preserved. The tool name itself signals intent in any audit trail.

Agent loop: `search("captcha stage")` → reads the endpoints → writes one code
block calling `ak.request(...)`, chaining as needed, in `execute` or
`execute_write`.

### v1 — local stdio server (the buildable target)

Lives in `authentik-agent-marketplace/mcp-servers/code-mode/` (the npm workspace
already scaffolded; `.mcp.json` + `SessionStart` deps-install hook already present).

- **Config / auth:** `AUTHENTIK_URL` + `AUTHENTIK_TOKEN` via env (the deployment
  model the community `authentik-mcp` validated). The token carries the admin's own
  permissions.
- **Schema source:** fetch `<AUTHENTIK_URL>/api/v3/schema/` at startup so discovery
  always matches the running instance's version, with a vendored `schema.yml`
  fallback. This *is* the zero-maintenance property — discovery follows the
  instance, nothing to regenerate here.
- **Sandbox — "the binding is the boundary":** in-process `node:vm` / `worker_thread`
  with globals stripped to just `ak` + `console` — no `fs`, no general `fetch`.
  `ak.request` is the only egress; in `execute` it is GET-only. Adversarial
  isolation is intentionally weak because the trust model is *an admin running code
  against their own instance with their own token* — the agent could do the same
  via any curated call, so the real control is the binding (read-only default +
  write gate), not the VM (per Ronacher).
- **Write gate:** `execute_write` triggers an MCP confirmation (elicitation) before
  running; on approval the call is write-armed for that invocation only. Every
  `execute_write` is logged locally.
- **Tools exposed:** `search`, `execute`, `execute_write`. Nothing else.
- **`@goauthentik/api`:** not on the critical path — `ak.request` is a generic
  authenticated fetch over `schema.yml` paths. The generated client's
  `Configuration`/runtime is an *optional* transport convenience, not the call
  surface.

### v2 — authentik-native OAuth endpoint (designed; built after v1 proves out)

This is where authentik being an identity provider pays off; it maps onto the
enterprise-mcp reference architecture almost 1:1.

- **Transport:** authentik serves a remote MCP endpoint (HTTP/SSE), e.g. `/mcp`, in
  the product.
- **Auth:** the MCP client performs **OAuth against authentik itself** (it is the
  OIDC provider) — no API-token handoff. The agent acts *as the authenticated user*.
- **Authorization = authentik's own RBAC.** `ak.request` runs server-side under the
  user's identity, so authentik's existing per-object / role permissions decide what
  the code may read or write. No new scope system to invent — reuse what authentik
  already enforces. (An MCP-level OAuth scope can still gate `execute_write` as a
  coarse on/off.)
- **Sandbox:** server-side, so real isolation is available (an isolate/worker pool),
  unlike v1's in-process VM.
- **Audit:** every `execute` / `execute_write` writes to authentik's **existing
  event log** — the same trail the `events-monitoring` admin skill already queries.

**Honest caveat:** v2 is product/backend work, release-gated, with a real security
surface (public-facing code execution behind an IdP). It is a roadmap design,
validated by v1 first — do not start it before the v1 captcha pivot passes.

---

## The pivot test: "add a captcha to my login flow"

This single hybrid task exercises the entire L1→L2→L3 loop and is the gate that
validates the architecture before broad build-out. In code-mode terms: the
`flows-stages` skill explains stages/flows (from the page `.md` Layer 1 ships) →
the agent calls `search("captcha stage", "flow stage binding")` → writes **one**
`execute_write` block that creates the captcha stage, finds the target flow, and
POSTs the binding — one confirmed call, no per-endpoint tools. MVP can run against
a mock server and a small `schema.yml` slice.

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
6. **L3 v1 — code-mode server core:** `search` (over `schema.yml`) + `execute`
   (read-only sandbox) + `execute_write` (confirmed). _Parallelizable with L2;
   depends only on the spec. On the critical path for the pivot test._
7. **🛑 GATE — captcha MVP end-to-end (the pivot).** Agent follows L2 → reads the
   captcha `.md` → `search`es the spec → writes one `execute_write` block (mock
   server OK). On failure, diagnose schema/prose clarity, not tooling.
8. **L1 — integrations subdomain.** _(Shipped — both sites live in PR #23360.)_
9. **L2 — wire `ak-admin`/`ak-dev` skills to the `llms.txt` entry points (L2→L1)
   and add the code-mode steering line (L2→L3).** _Parallelizable._
10. **L3 v2 — authentik-native OAuth endpoint.** _Only_ after the v1 pivot passes;
    product/backend effort, separate spec + plan.

---

## Cross-cutting

- **Distribution:** Claude Code + Cursor manifests already in the marketplace; the `ak-admin`/`ak-dev` plugins serve both.
- **Security (v1):** local stdio keeps the admin's token in their own environment;
  the sandbox exposes only `ak` (no `fs`/`fetch`); `execute` is GET-only;
  `execute_write` is confirmed per call and logged. The binding is the boundary.
- **Security (v2):** OAuth against authentik; authorization is authentik's own
  RBAC under the user's identity; every call audited to the event log.
- **Maintenance thesis:** docs (`.md` + indexes) and the API surface
  (`search` over the live `schema.yml`) both come straight from authentik each
  release; L2 is thin glue and L3 has no per-endpoint code to patch. Steady-state
  human upkeep approaches zero.

## Open questions for plan stage

- **L3:** how `search` ranks/filters operations from `schema.yml` (keyword over
  path+summary+tags; how much schema slice to return per hit without bloating context).
- **L3:** the exact `node:vm` vs `worker_thread` sandbox choice and how globals are
  stripped to just `ak` + `console`; how the MCP confirmation (elicitation) for
  `execute_write` is surfaced across Claude Code / Cursor.
- **L3:** `ak.request` transport — plain authenticated `fetch` vs. `@goauthentik/api`'s
  `Configuration` runtime; how `/api/v3/schema/` fetch-at-startup vs. vendored
  fallback is selected.
- **L2 wiring:** confirm the single steering line per `ak-admin` skill and the stable
  `llms.txt` entry-point URLs (depends only on Layer 1, already shipped).
