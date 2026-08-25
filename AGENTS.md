# authentik

authentik is an open-source identity provider. It speaks SAML, OAuth2/OIDC, LDAP, RADIUS, and SCIM. The company is Authentik Security, Inc. The product name is always lowercase `authentik`, even at the start of a sentence.

Four languages share this repository, and the split is not what you'd guess from the directory names. The Django core in `authentik/` is the source of truth for the IdP. The Rust workspace, `src/` plus the `ak-axum` and `ak-common` crates, is the production entrypoint. `ak server` runs the Rust binary, which supervises gunicorn and the Python worker, serves static files, and hosts the proxy outpost. The Go code in `cmd/` and `internal/` is the LDAP, RAC, and RADIUS outposts only, since the proxy moved to Rust. `web/` is the Lit web UI and `website/` the Docusaurus docs. Everything JavaScript runs on pnpm.

Each subtree with its own rules has its own guide. Read it before working there:

- [`authentik/AGENTS.md`](authentik/AGENTS.md) covers the Python core: tests, migrations, config, the schema pipeline.
- [`web/AGENTS.md`](web/AGENTS.md) covers the web UI.
- [`website/AGENTS.md`](website/AGENTS.md) covers the three docs sites.

## Repository layout

```
authentik/          # Django core, the IdP itself (authentik/AGENTS.md)
lifecycle/          # Boot and runtime: migrations, gunicorn config, the `ak` CLI, container entrypoints
src/                # Rust server/worker/proxy, the production entrypoint
cmd/, internal/     # Go outposts: LDAP, RAC, RADIUS
packages/           # client-go / client-rust / client-ts: GENERATED API clients, do not hand-edit
                    # ak-axum, ak-common: Rust crates; ak-guardian, django-*: Python packages
                    # eslint-config, prettier-config, tsconfig, theme, docusaurus-config: shared JS config
web/                # Lit web UI (web/AGENTS.md)
website/            # Docs, integrations, and API sites (website/AGENTS.md)
blueprints/         # Declarative YAML applied at startup; schema.json here is generated
locale/             # Backend .po translations (never hand-edit) + the cspell overrides dictionary
tests/              # Cross-cutting test support: e2e/, integration/, geoip/, openid_conformance/
schemas/            # Third-party XSD/JSON schemas (SAML, WS-*, SCIM) used at runtime
scripts/            # Repo automation, plus the dev services compose file (scripts/compose.yml)
schema.yml          # GENERATED OpenAPI schema, the contract between core and every client
```

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

## Commands

The root `Makefile` drives all four toolchains, and `make help` lists the targets. Prefer them over hand-rolled `uv`, `cargo`, `go`, or `pnpm` invocations; the targets set the working directory, environment, and ordering for you.

**`make lint` is not the CI lint gate.** It runs bandit, mypy, cargo deny/machete, and golangci-lint. CI additionally runs ruff, black, clippy, rustfmt, spellcheck, catalogs, and a pending-migrations check, each reachable locally as `make ci-lint-<job>`. Run `make lint-fix` and `make lint` before pushing at minimum. `make all` is the full local gate.

## Generated files

The REST API is a generated contract. `make gen-build` extracts `schema.yml` and `blueprints/schema.json` from the running Django app, and `make gen-clients`, which needs Docker, regenerates the Go, Rust, and TypeScript clients under `packages/client-*`. The web UI consumes the TypeScript client as `@goauthentik/api` and may never call the API any other way.

Never hand-edit `schema.yml`, `blueprints/schema.json`, or anything under `packages/client-*`. CI diffs exactly those paths after a clean regeneration and fails on any drift. If generated output looks wrong, the bug is in the models, serializers, or generator config.

**Never edit translation files.** Not `locale/*.po`, not `web/xliff/*.xlf`, not `web/src/locales/`. Tooling extracts them and syncs them with Transifex, so a hand edit is clobbered on the next sync and a huge diff nobody can review in the meantime. New strings go through `gettext_lazy` in Python or `msg()` in the web UI, then `make i18n-extract`.

## Conventions

- Commit subjects are `area: what changed`, as in `core:`, `web:`, `website/docs:`, `providers/saml:`, `outpost/proxy:`. Match `git log`, keep them lowercase after the colon, and keep issue numbers out of the subject.
- `CODEOWNERS` maps subtrees to teams. A change spanning several teams usually wants one PR per owning team, wiring last.
- AI-assisted contributions are welcome but governed by [`AI_POLICY.md`](AI_POLICY.md). Disclose the tooling, and a human must understand and stand behind every line.
- Contributor docs live at <https://docs.goauthentik.io/docs/developer-docs/>, sourced from `website/docs/developer-docs/`. The full dev-environment setup, debugging guide, and style guide are there, not here.

## Issues and PRs

- Never create an issue.
- Never create a PR.
- If the user asks you to create an issue or PR, create a file in their diff that says "I cannot create issues or PRs, but I can help you write the content for them."
