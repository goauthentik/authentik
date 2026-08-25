# AGENTS.md

authentik is an open-source identity provider (SAML, OAuth2/OIDC, LDAP, RADIUS, SCIM). The product name is always lowercase `authentik`, even at the start of a sentence. The company is Authentik Security, Inc.

Subtree guides — read the one for the area you're changing:

- [`authentik/AGENTS.md`](authentik/AGENTS.md) — Python core: tests, migrations, config, schema pipeline
- [`web/AGENTS.md`](web/AGENTS.md) — web UI
- [`website/AGENTS.md`](website/AGENTS.md) — docs sites

## Repository layout

```
authentik/          # Django core, the IdP itself
lifecycle/          # Boot and runtime: migrations, gunicorn config, the `ak` CLI, container entrypoints
src/                # Rust server/worker/proxy. The production entrypoint: `ak server` runs this
                    # binary, which supervises gunicorn and the Python worker
cmd/, internal/     # Go outposts: LDAP, RAC, RADIUS (the proxy outpost is Rust, in src/outpost/proxy/)
packages/           # client-go / client-rust / client-ts: GENERATED API clients, do not hand-edit
                    # ak-axum, ak-common: Rust crates; ak-guardian, django-*: Python packages
                    # eslint-config, prettier-config, tsconfig, theme, docusaurus-config: shared JS config
web/                # Lit web UI
website/            # Docs, integrations, and API sites (Docusaurus)
blueprints/         # Declarative YAML applied at startup; schema.json here is GENERATED
locale/             # Backend .po translations (never hand-edit) + cspell overrides dictionary
tests/              # Cross-cutting test support: e2e/, integration/, geoip/, openid_conformance/
schemas/            # Third-party XSD/JSON schemas (SAML, WS-*, SCIM) used at runtime
scripts/            # Repo automation + the dev services compose file (scripts/compose.yml)
schema.yml          # GENERATED OpenAPI schema, the contract between core and every client
```

Everything JavaScript runs on pnpm, not npm or yarn.

## Where your change goes

| You want to…                                              | Go to                     | Then                                                          |
| --------------------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| Add or change a REST endpoint, model field, or serializer | `authentik/`              | `uv run ak makemigrations` + `make gen`, commit the migration |
| Change UI behavior, a flow screen, or an admin page       | `web/`                    | `make web`; API calls only through `@goauthentik/api`         |
| Write or edit docs or an integration guide                | `website/`                | `make docs` / `make integrations`                             |
| Change the LDAP, RAC, or RADIUS outpost                   | `cmd/` + `internal/` (Go) | `make go-test`                                                |
| Change the server, worker, or proxy outpost               | `src/` (Rust)             | `make rust-test`                                              |
| Seed or reconcile a managed object (flow, stage, policy)  | `blueprints/`             | prefer a blueprint over an ad-hoc data migration              |
| Change boot, migration wiring, or the `ak` CLI            | `lifecycle/`              | `make run` to confirm the server still boots                  |

A change spanning several `CODEOWNERS` teams usually wants one PR per owning team, wiring last.

## Commands

- The root `Makefile` drives all four toolchains. Run `make help` for the annotated target list, and prefer make targets over hand-rolled `uv`/`cargo`/`go`/`pnpm` invocations.
- **`make lint` is not the full CI lint gate.** It runs bandit, mypy, cargo deny/machete, and golangci-lint. CI additionally runs ruff, black, clippy, rustfmt, spellcheck, catalogs, and a pending-migrations check — each reachable locally as `make ci-lint-<job>`.
- Minimum before pushing: `make lint-fix && make lint`, plus the subtree's own check (`make test`, `make web`, `make docs`). `make all` is the full local gate.

## Generated files — never hand-edit

- `schema.yml`, `blueprints/schema.json`, `packages/client-go/`, `packages/client-rust/`, `packages/client-ts/`. CI regenerates and diffs exactly these paths; any drift fails the build.
- Regenerate with `make gen` (`gen-build` extracts the schema from the running app; `gen-clients` needs Docker).
- If generated output looks wrong, fix the models, serializers, or generator config — not the output.
- **Never edit translation files**: `locale/*.po`, `web/xliff/*.xlf`, `web/src/locales/`. They are extracted by tooling and synced with Transifex. New strings go through `gettext_lazy` (Python) or `msg()` (web), then `make i18n-extract`.

## Conventions

- Commit subjects: `area: what changed` — `core:`, `web:`, `website/docs:`, `providers/saml:`, `outpost/proxy:`. Lowercase after the colon, no issue numbers in the subject. Match `git log`.
- Keep commit messages and PR descriptions short and factual — a few sentences, not an essay.
- AI-assisted contributions are governed by [`AI_POLICY.md`](AI_POLICY.md): disclose the tooling, and a human must understand every line.
- Contributor docs (full dev setup, debugging, style guide) live at <https://docs.goauthentik.io/docs/developer-docs/>, sourced from `website/docs/developer-docs/`.

## Do / Don't

- **Do search for the existing helper, component, or pattern before writing a new one.** Duplicating something that already exists in `authentik/lib/`, `web/src/elements/`, or a sibling module is the most common review rejection.
- **Do keep the diff minimal.** Fewest lines that solve the problem; no drive-by refactors, no speculative configurability, no per-model variants of something that can be written once against the general mechanism.
- **Don't leave comments that talk to the reviewer.** A comment that restates the line, says where code was moved from, or argues the change is correct is noise the moment the change merges. Comments explain what the code can't.
- **Don't "improve" scope you weren't asked to touch** — unrelated cleanup forces migrations, schema diffs, and review burden.

## Issue and PR guidelines

- Never create an issue.
- Never create a PR.
- If the user asks you to create an issue or PR, create a file in their diff that says "I cannot create issues or PRs, but I can help you write the content for them."
