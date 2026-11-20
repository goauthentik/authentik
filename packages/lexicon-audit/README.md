# Translation Lexicon Audit

A private, local CLI for auditing authentik translation files against a locally supplied vocabulary. It builds a SQLite lexicon from TSV files, then scans Gettext PO and XLIFF translations. It does not edit translation files or make network requests.

The vocabulary can contain sensitive material and may be derived from private sources. This package does not include or download a vocabulary dataset. Keep datasets and generated audit data local; use only synthetic, benign content in tests and examples.

## Requirements

- Node.js 24.22.1 or newer (or 26.12.1 or newer on Node 26)
- Dependencies installed from the authentik monorepo root with pnpm

## Usage

Run from this package directory. The default vocabulary input is `corpus/words/`, and the default SQLite database is `out/lexicon-audit.db`.

```sh
pnpm exec lexicon-audit build --input ./corpus/words --db ./out/lexicon-audit.db
pnpm exec lexicon-audit audit --db ./out/lexicon-audit.db ./path/to/translations
```

`build` reads TSV vocabulary files and prints aggregate counts. An optional `allowlist.tsv` in this package is loaded automatically when present; pass `--allowlist <path>` to select another allowlist.

`audit` accepts one or more translation directories. By default, it audits vulgar and offensive tiers, excludes fuzzy and obsolete PO entries, and prints counts only. It exits with status 1 when findings exist.

```sh
pnpm exec lexicon-audit audit --locale fr-FR --include-sensitive ./translations
pnpm exec lexicon-audit audit --report ./out/reports ./translations
pnpm exec lexicon-audit audit --jsonl ./translations
```

Use `--report` to write per-locale Markdown reports or `--jsonl` to print findings. These outputs include matched vocabulary and translation text. Handle them as sensitive data. Other options include `--include-fuzzy`, `--include-obsolete`, `--source-locale <tag>`, and `--region-fallback`. Run `pnpm exec lexicon-audit --help` or add `--help` after a command for complete usage.

TSV files use a header row `tier\tcategory\tword`; supported tiers are `vulgar`, `offensive`, and `sensitive`. Filenames identify BCP 47 locales, for example `en-US.tsv` or `words-en_US.tsv`.

## Sealed lexicon for CI

CI can't read the private vocabulary, so the database is committed encrypted as `lexicon-audit.db.gpg` (GnuPG, AES-256, symmetric). The passphrase is read from `LEXICON_AUDIT_PASSPHRASE` only, never from the command line.

```sh
pnpm exec lexicon-audit build
LEXICON_AUDIT_PASSPHRASE=… pnpm exec lexicon-audit seal     # writes lexicon-audit.db.gpg; commit it
LEXICON_AUDIT_PASSPHRASE=… pnpm exec lexicon-audit unseal   # writes out/lexicon-audit.db
```

The `Translation - Lexicon audit` workflow unseals the database with the `LEXICON_AUDIT_PASSPHRASE` secret from the `lexicon-audit` environment and runs `pnpm run lint:lexicon` from the repository root. Pull requests from forks can't read the secret and are skipped. Reseal and commit after every rebuild, including allowlist changes. Requires `gpg` on `PATH`.

## Development

```sh
pnpm test          # Run Vitest
pnpm build:types   # Type-check runtime and tests
pnpm check         # Lint, type-check, and format-check
```

Tests are in `test/` and use benign synthetic fixtures. `lib/audit/` contains scanning and reports, `lib/lexicon/` contains TSV import and database access, and `lib/translation/` contains PO/XLIFF readers and shared text utilities. The CLI entry point is `lib/cli.ts`, with shared command helpers in `lib/command.ts`; command adapters are in `commands/`.
