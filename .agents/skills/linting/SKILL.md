---
name: linting
description: >
    Fix lint and formatting before you push, and reproduce a failing CI lint or type check
    locally. Maps every CI lint job to the local command: Python (black, ruff, mypy, bandit),
    Go (golangci-lint), Rust (rustfmt, clippy, cargo deny, cargo machete), web (oxlint, oxfmt,
    tsc, lit-analyse), docs, spelling (cspell), pnpm catalogs, locales, pending migrations and
    the generated schema. Use when someone asks "fix the lint", "CI lint failed", "mypy is
    red", "clippy fails locally but not in CI", "cspell flagged a word", or "schema is out of
    date". Other skills cover the rest: testing for test runs, dev-environment for tool setup,
    contributing for PR conventions, and release for release builds.
---

# authentik linting and type checks

## Purpose

CI runs one lint job per tool, each a thin `make ci-lint-<job>` wrapper. Locally you can
run the same targets, so a red CI job is almost always reproducible from the repo root.
This skill gives the one-shot fix, then the job-to-command map, then the traps.

Steps are tagged: `[shell]` local command, `[verify]` check before moving on.

## 1. Fix everything before pushing

1. **[shell]** Backend and Rust: `make lint-fix` (black, `ruff check --fix`, and
   `cargo +nightly fmt`).
2. **[shell]** Web, if you touched `web/`: `make web` (oxfmt write, `oxlint --fix`,
   lit-analyse, tsc).
3. **[shell]** Docs, if you touched `website/`: `make docs-lint-fix` (cspell, then website
   lint and format).
4. **[shell]** If you changed a model, serializer or viewset: `make gen` and commit
   `schema.yml`, `blueprints/schema.json` and `packages/client-*`. Commit the migration
   too.
5. **[verify]** `make lint` (bandit, mypy, cargo deny, cargo machete, golangci-lint).
6. **[verify]** `make lint-changed` runs every CI lint job that covers the files changed
   since `origin/main`, with CI's commands, and lists the jobs it couldn't map (`fix=1`
   applies fixes first). From an agent, the `akdev_lint` tool does the same.

`make all` chains `lint-fix lint gen web test`. It is the PR template's checklist item,
but it runs the whole Python test suite, so it is slow.

The fixers leave a gap: `make lint` doesn't run `black --check`, `ruff check`, clippy or
rustfmt in check mode. Run those CI targets directly when they're the ones failing.

## 2. Reproduce a failing CI job

The `lint` matrix in `.github/workflows/ci-main.yml` runs `make ci-lint-${{ matrix.job }}`.
Copy the job name from the failing check and run the same target.

| CI job (`ci-main.yml` unless noted)        | Local command                                                                                                | Auto-fix                                 |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| `lint (black)`                             | `make ci-lint-black`                                                                                         | `make lint-fix`                          |
| `lint (ruff)`                              | `make ci-lint-ruff`                                                                                          | `make lint-fix`                          |
| `lint (mypy)`                              | `make ci-lint-mypy` (`mypy --strict`)                                                                        | none                                     |
| `lint (bandit)`                            | `make ci-lint-bandit`                                                                                        | none                                     |
| `lint (rustfmt)`                           | `make ci-lint-rustfmt`                                                                                       | `make lint-fix-rust`                     |
| `lint (clippy)`                            | `make ci-lint-clippy` (`-D warnings`, all targets)                                                           | none                                     |
| `lint (cargo-deny)`                        | `make ci-lint-cargo-deny`                                                                                    | none                                     |
| `lint (cargo-machete)`                     | `make ci-lint-cargo-machete`                                                                                 | remove the unused dependency             |
| `lint (spellcheck)`                        | `make ci-lint-spellcheck`                                                                                    | fix the word (see Gotchas)               |
| `lint (catalogs)`                          | `make ci-lint-catalogs`                                                                                      | align the pins it names                  |
| `lint (locales)`                           | `make ci-lint-locales`                                                                                       | `make gen-locales`                       |
| `lint (oxlint-fixtures)`                   | `make ci-lint-oxlint-fixtures`                                                                               | none                                     |
| `lint (pending-migrations)`                | `make ci-lint-pending-migrations`                                                                            | `uv run python -m manage makemigrations` |
| `lint-migrations`                          | `make ci-lint-migrations MIGRATIONS_BASE=<base ref>`                                                         | none                                     |
| `test-gen` ("ensure schema is up-to-date") | `make migrate gen-build gen-clients`, then `git diff -- schema.yml blueprints/schema.json packages/client-*` | commit the diff                          |
| `ci-web.yml` Lint                          | `pnpm --dir web run lint:check`                                                                              | `pnpm --dir web run lint`                |
| `ci-web.yml` Check formatting              | `pnpm --dir web run format:check`                                                                            | `pnpm --dir web run format`              |
| `ci-web.yml` Check types                   | `pnpm --dir web run tsc`                                                                                     | none                                     |
| `ci-web.yml` lit-analyse                   | `pnpm --dir web run lit-analyse`                                                                             | none                                     |
| `ci-docs.yml` lint (`check`)               | `pnpm --dir website run check`                                                                               | `make docs-lint-fix`                     |
| `ci-outpost.yml` golangci-lint             | `golangci-lint run -v --config .github/golangci.yml`                                                         | none                                     |

For a quick read-only web check, `make web-check` runs `lint:check` and `format:check`.
`make docs-check` does the same for the docs plus `build:types`.

## Web tooling

The web UI uses **oxlint** and **oxfmt** in place of ESLint and Prettier. Configs are
`oxlint.config.ts` and `oxfmt.config.ts` at the root, built from
`packages/oxlint-config` and `packages/oxfmt-config`. The root `package.json` lints only
`scripts/node` and root config files. `pnpm run check` at the root runs every workspace's
`check`, plus `build:types`, catalogs and spellcheck.

Read the diff after `oxlint --fix`. Its autofix can change meaning. It once stripped
`[...typedArray]` spreads in tests.

## Gotchas

- **cspell runs in typo-only mode.** `cspell.config.jsonc` sets
  `unknownWords: "report-common-typos"`. Unknown words pass, so product names and jargon
  need no dictionary entry. Only common misspellings (shown with a `fix:`) and
  `flagWords` (British spellings) fail. If the flagged word is real, for example an
  upstream API name, add it to `locale/en/dictionaries/overrides.txt`. A `flagWords` hit
  can't be overridden by a dictionary: add an `ignoreRegExpList` entry or a
  `cspell:disable-next-line` comment. Python is only checked inside comments.
- **Homebrew `cargo` shadows the pinned toolchain.** `rust-toolchain.toml` pins the
  channel, but `/opt/homebrew/bin/cargo` ignores rustup. Clippy then reports phantom
  `this lint expectation is unfulfilled` errors on `#[expect(...)]` attributes. Check
  `cargo clippy --version` against `rustc --version`. Fix by putting the toolchain's bin dir
  first: `export PATH="$(dirname "$(rustup which cargo)"):$PATH"`.
- **rustfmt needs nightly.** `lint-fix-rust` and `ci-lint-rustfmt` call `cargo +nightly
fmt`. Install it once: `rustup toolchain install nightly --profile minimal --component
rustfmt`. Never run bare `cargo fmt`: without `--config-path .cargo/rustfmt.toml` it
  reorders imports and rewrites the generated `packages/client-rust/`.
- **Rust tests or builds abort with a dyld error** about `Python3.framework/Versions/3.9`.
  The `core` feature links pyo3 against Xcode's Python. Set `PYO3_PYTHON` to the project's
  Python 3.14 interpreter.
- **The proxy image builds a feature set PR CI doesn't lint.**
  `lifecycle/container/proxy.Dockerfile` builds with `--no-default-features --features
proxy`, and this once broke a release candidate. If you touch `src/`
  or `packages/ak-*`, also run
  `cargo clippy --workspace --no-default-features --features proxy -- -D warnings`. Put
  server-only code behind `#[cfg(feature = "core")]`.
- **mypy is `--strict`.** New Python needs full annotations. A `# type: ignore` needs a
  specific error code and a reason a reviewer will accept.
- **`pending-migrations` needs the runtime.** It imports Django, so it needs a working
  config and database (`make gen-dev-config`, Postgres up).
- **`lint-migrations` compares against a base.** CI uses the previous stable tag. Locally,
  it defaults to `origin/main`. Fetch first or it diffs against a stale ref.
- **`ci-lint-*` targets print tool versions first** (`ci--meta-debug`). A missing `uv`,
  `cargo` or `node` shows up there as a missing version line, before any lint output.

## Style that lint won't catch

Reviewers also ask for:

- Code comments that are one short line stating a non-obvious fact. The reasoning and history
  go in the commit message.
- In TypeScript: multiline JSDoc only, explicit `public`/`protected` on class members,
  braces on every `if` body, `parseInt(x, 10)` over `Number(x)`, and a well-known library
  over hand-rolled parsing of standard formats.
