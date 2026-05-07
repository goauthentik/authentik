# AGENTS.md

This is **authentik** — an open-source Identity Provider. The codebase spans a
Django backend, Go outposts, Rust components, and a Lit/TS web UI, with pieces
wired together through Django signals, Channels, blueprints, flow plans, and a
generated API client. It's a lot of moving parts. Before changing something
non-trivial, pause to think about what else touches it: a model edit can ripple
through serializers, signals, blueprints, and the generated TS client.

## Commits

Format the subject as `area: short message`. Skip the long body unless
something genuinely needs explaining. The `area` is wherever you worked, e.g.:

- `root:` — repo-wide changes
- `core:` — `authentik/core` and dependency bumps
- `api:` — API surface
- `web:`, `web/admin:`, `web/flows:`, `web/stages:` — frontend
- `website:`, `website/docs:`, `website/integrations:`
- `stages/invitation:`, `providers/oauth2:`, `providers/oauth:` — feature modules
- `enterprise/providers/ssf:`
- `lifecycle/worker_process:`
- `tenants:`, `ci:`, `docs:`, `translate:`

When the user gives you a PR or issue for the bug being fixed, add a
`Closes: #NNN` trailer on its own line — don't tack `(#NNN)` onto the subject.

**Never** include customer information or any potentially sensitive *content*
taken from internal sources — verbatim or reworded — anywhere in the repo
(code, comments, commit messages, PR descriptions, docs) unless explicitly
allowed. This covers customer names, support ticket contents, quoted Slack
messages, private incident details, and similar.

Links are fine. A Slack permalink, a GitHub issue link, or an internal ticket
URL in a commit message or PR description is good context — it's the
sensitive *content* that must not be copied into the repo. When in doubt,
leave the content out and link instead.

A commit should be a finished, working unit. Don't commit half-done work.
Before committing, run whatever applies:

- `make lint-fix`
- `make gen` if you touched models or serializers
- `make web` if you touched `web/`
- `make docs` if you touched `website/docs/`
- `make integrations` if you touched `website/integrations/`
- `./manage.py makemigrations --check` — no pending migrations

The `Makefile` has more targets per area (tests, Go, Rust) — use them when
relevant.

## Don't hand-edit generated or vendored files

Run `make gen` instead. Off-limits:

- `schema.yml` (OpenAPI)
- `gen-ts-api/`
- `packages/client-go/`, `packages/client-ts/`, `packages/client-rust/`
- `schemas/` — these are upstream SAML / SCIM / WS-* specs, not ours

If the output looks wrong, fix the source (models, serializers, generator
config) and regenerate.

## Migrations

Generate them with `./manage.py makemigrations`. Don't hand-write or hand-edit
migration files unless the user specifically asks (data migrations, squashes,
or repairing a bad one). Read what Django produced before committing — autogen
sometimes catches more than you intended.

## Localization

Anything user-visible needs to be translatable:

- Python: `from django.utils.translation import gettext_lazy as _`, then `_("...")`
- TS / Lit: `msg("...")` from `@lit/localize`
- Django templates: `{% trans %}` / `{% blocktrans %}`

No raw English strings in user-facing surfaces.

## Tests, proportionate

Size tests to the code. A 28-line function doesn't need a 400-line test file.
Cover meaningful behavior and obvious edge cases; don't pad for coverage or
re-test the framework. Mechanical changes (renames, type tweaks) usually ride
on existing tests.

## Reuse what's already there

There's a large pool of helpers — find them before writing new ones.

- **Django first.** `django.utils`, `django.shortcuts`, the ORM, the auth
  framework — most generic things already exist there.
- **Then authentik.** `authentik/lib/`, `authentik/core/`, and the feature
  module you're working in.
- **Call helpers, don't inline them.** If `plan.to_redirect()` exists, use it
  instead of rebuilding the redirect at every call site. Same goes for
  permission checks, flow plan helpers, event logging, serializer mixins, etc.

## DRY, with judgment

Deduplicate behavior, not boilerplate. Some things are cheap to restate and
often clearer that way — serializers, simple model definitions, view glue,
short config blocks — don't twist them through inheritance or shared bases
just to save lines. But duplicated *behavior* — a function body copy-pasted
across modules, a permission check reimplemented inline, a redirect built from
scratch next to a helper that already does it — should collapse to one place.
If changing the logic later would mean hunting down every copy, it belongs in
one spot.
