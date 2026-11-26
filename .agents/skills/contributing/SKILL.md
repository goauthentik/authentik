---
name: contributing
description: >
    Take a branch to a well-formed authentik pull request: branch names, the
    `area: summary` commit and PR title, the PR template and description style, the checks
    CI requires, licensing (neither a CLA nor a DCO sign-off), the AI policy, splitting PRs by
    CODEOWNERS, backport labels, and commit attribution. Use when someone asks "open a PR
    for this", "what should the PR title be", "write the PR description", "does this need
    a backport", "should I split this PR", or "do I need to sign a CLA". The linting and
    testing skills run the checks, community covers where to ask questions, and release
    covers publishing a release.
---

# How to contribute to authentik

## Purpose

PRs are squash-merged, so the PR title becomes the commit on `main` and feeds the
generated changelog. The title, labels and scope matter more than the individual
commits. The canonical guide is
[Contributing to authentik](https://docs.goauthentik.io/developer-docs/contributing/)
(`website/docs/developer-docs/contributing.mdx`). Read it first. This skill adds what the
maintainers do in practice.

Steps are tagged: `[shell]` local command, `[gh]` GitHub UI or `gh`, `[verify]` check
before moving on, `[ask]` confirm with the person first.

## 1. Branch

1. **[shell]** Never work on `main`. Outside contributors open PRs from a fork's feature branch.
   The PR template rejects PRs from `main`.
2. **[shell]** Name the branch after the area, the way maintainers do:
   `web/bug/<topic>`, `web/maint/<topic>`, `website/docs/<topic>`,
   `providers/oauth2/<topic>`. The docs' example `feature/<name>` also works.

## 2. Title and commits

Format: `<area>: <verb> <description>`, lowercase after the colon and without a trailing period.
The area is the package path, the same structure as `authentik/` and the top-level
folders. Real titles from `git log`:

- `outposts: close docker client connection on exit`
- `core: discard sessions that reference moved modules`
- `web/elements: default a dialog's invoker to the element that opened it`
- `stages/authenticator_webauthn: parse MDS statements without user verification details`
- `website/integrations: Arcane: update for Arcane 3.x`
- `ci: leave rust build-warnings setting default`

Several areas: join them, as in `core, web: update translations`.
Security fixes use `security:`. The changelog keeps those entries,
so don't bury a CVE fix under another area.
Because of the squash merge, commits inside the PR can have any message.

Commit attribution: don't add a Claude or other AI co-author trailer.
Credit human collaborators with `Co-authored-by:` instead.

## 3. Description

Fill `.github/pull_request_template.md`. Maintainers keep it short:

```md
## Details

This PR fixes {{what}} in {{where}}. {{At most one sentence on the cause.}}

- Keep the host's `value` as the selection; store user choices in state.
- Compare selections by option name.

closes #1234
```

- One sentence that starts "This PR …", then one terse imperative bullet per change.
- Short, independent sentences. Avoid ", so …" and ", which …" chains.
- No testing paragraph.
- `closes #N` closes an issue on merge. `refs #N` links without closing.
- Outside contributors must keep the checklist and the AI disclosure: `AI_POLICY.md`
  requires saying which AI tools were used and how much.
  A human must understand and be able to explain every line.

## 4. Before pushing

1. **[shell]** Lint and format the areas you touched (see the linting skill).
2. **[shell]** Model, serializer or viewset changes: `make gen` and commit `schema.yml`,
   `blueprints/schema.json`, `packages/client-*` and the migration. CI's `test-gen` job
   fails on any diff. `make check-gen` tells you whether anything is still stale.
3. **[shell]** Docs changes: `make docs` (spellcheck, format, build).
4. **[verify]** Tests cover what a customer does through the product. Don't add a test
   that only mirrors the patch.

## 5. Checks CI runs

- `ci-main.yml`: the `lint` matrix, `lint-migrations`, `test-gen`, migrations
  (including from the last stable release), unit tests on several PostgreSQL versions,
  integration and e2e suites, and container builds.
- `ci-web.yml`: oxlint, tsc, oxfmt, lit-analyse, build and unit tests.
- `ci-docs.yml`, `ci-outpost.yml`, `ci-api-docs.yml`: docs, Go outposts, API docs.
- `qa-codeql.yml`, `qa-semgrep.yml`, `qa-dependency-review.yml`: security scanning.

If a failure looks unrelated to your change, comment on the PR with the reason. A
maintainer reruns it. Maintainers can rerun failed jobs with `gh run rerun <id> --failed`. e2e jobs
are the usual flakes.

## 6. License terms

There's no CLA and no DCO sign-off. No workflow checks for either. `LICENSE` is MIT for
most of the repo, with exceptions: `website/` is CC BY-SA 4.0, `authentik/enterprise/` has
its own license, and client-side JavaScript is MIT Expat. Your contribution falls under the
license of the directory it lands in.

## 7. Split by CODEOWNERS

`CODEOWNERS` assigns `@goauthentik/backend` (Python, Go, Rust, `blueprints/`, `scripts/`),
`@goauthentik/frontend` (`web/`, web packages), `@goauthentik/infrastructure`
(`.github/`, `Makefile`, `lifecycle/container/`, `lifecycle/aws/`) and `@goauthentik/docs`
(`website/`). A change spanning several owners is best split into one PR per team. Merge the
enabling or wiring PR last. For a dependent series, a stacked set of PRs works well.

## 8. Backports

Add a `backport/version-<year>.<minor>` label (list them with
`gh label list --search backport`) to a PR on `main`.
After merge, the `authentik-cherry-pick` app opens `cherry-pick/<pr>-to-version-<year>.<minor>`.
A failed cherry-pick needs a manual PR against the release branch.
Supported versions are listed in `SECURITY.md`. `backport/main` brings a fix made on a release branch forward.

## Gotchas

- **Teammates push to shared PR branches.** Before a rebase and force-push, run
  `git fetch` then `git log --format='%h %an %s' HEAD..origin/<branch>`.
  If it lists commits, rebase onto `origin/<branch>`. `--force-with-lease` doesn't help once the fetch
  has moved the tracking ref.
- **Push one branch per `git push`.** A push with several refs at once hits a repository rule (GH013).
- **Dependabot and translation PRs** follow their own titles (`web: bump …`,
  `translate: Updates for …`). Don't copy those as a model.
- **[ask]** Confirm before anything visible to others: opening or retitling a PR,
  force-pushing, or labeling for backport.
