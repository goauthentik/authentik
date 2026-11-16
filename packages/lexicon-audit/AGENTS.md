# Repository Guidelines

## Project Structure & Module Organization

`lexicon-audit` is a private TypeScript package in the authentik monorepo. `lib/audit/` contains scanning, matching, reporting, and the counts summary; `lib/lexicon/` contains vocabulary import, storage, and allowlisting; `lib/translation/` contains PO/XLIFF readers and shared text/locale utilities. The CLI entry point is `lib/cli.ts`, shared command helpers are in `lib/command.ts`, command adapters are in `commands/`, and Vitest tests and fixture helpers are in `test/`. `package.json` defines scripts and aliases. TypeScript extends the shared authentik config; `oxlint.config.ts`, `oxfmt.config.ts`, and `vite.config.ts` configure tooling.

Keep test inputs synthetic and benign. Never add private lexicon dumps or print flagged terms or matched translation text in logs, snapshots, or committed fixtures. Treat audit inputs as read-only and keep generated databases and reports outside version control.

## Build, Test, and Development Commands

Run commands from this package directory with the monorepo's pnpm installation:

- `pnpm test` — run Vitest once; `pnpm test:watch` starts watch mode.
- `pnpm build` — run the CLI build command.
- `pnpm build:types` — type-check runtime and test code.
- `pnpm lint:check` and `pnpm format:check` — check Oxlint and Oxfmt rules.
- `pnpm check` — run lint, type, and format checks together.

## Coding Style & Naming Conventions

Use TypeScript ESM and Node built-ins where practical. Follow shared authentik Oxfmt/Oxlint settings; preserve existing four-space JSON formatting and straightforward imports. Use descriptive camelCase for variables/functions, PascalCase for types/classes, and kebab-case command/module filenames. Keep CLI output aggregate-only and deterministic.

## Testing Guidelines

Tests use Vitest with Node environment and `test/*.test.ts` naming. Add focused tests alongside the behavior being changed; use helpers in `test/helpers.ts` for temporary fixture trees and benign PO, XLIFF, or TSV content. Run `pnpm test` and `pnpm check` for relevant changes. No coverage threshold is configured here.

## Commit & Pull Request Guidelines

Monorepo history uses concise, scoped conventional-style subjects, often `area: action (#number)` (example: `packages: update audit behavior`). Keep commits focused. Pull requests should describe behavior and validation, note privacy or data-handling implications, and include CLI examples when changing options. Do not include sensitive vocabulary or real audit output in descriptions, screenshots, or logs. Follow repository instructions: do not create issues or pull requests.

## Security & Configuration

The package is private and may process sensitive translation content. Do not add network calls, commit local source datasets, or expose raw findings by default. The one committed copy of the lexicon is `lexicon-audit.db.gpg`, encrypted with `seal`; never commit the decrypted database or the passphrase. Validate paths and input formats, and preserve read-only behavior for source files.
