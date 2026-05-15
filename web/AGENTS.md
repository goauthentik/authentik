# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **authentik WebUI** — the default web interface for the authentik identity server. It is a TypeScript monorepo using Lit web components and PatternFly 4 design system.

There are three distinct UI applications, each with its own base URL and router:

- **Flow** (`/if/flow/`) — Form orchestration for login, signup, password reset, etc.
- **User** (`/if/user/`) — End-user portal for applications and profile settings
- **Admin** (`/if/admin/`) — Server administration and configuration

All three share three core context objects:

- **Config** — Server configuration and user permissions
- **CurrentTenant/Brand** — Theme, logos, favicon, default flows
- **SessionUser** — Logged-in user with impersonation support

## Commands

### Development

```bash
npm run watch          # Build + watch locales and bundler (main dev workflow)
npm run storybook      # Storybook dev server on port 6006
```

### Build

```bash
npm run build          # Production build to dist/
npm run build-locales  # Compile i18n translations
```

### Testing

```bash
npm test               # Vitest: unit tests (Node) + browser tests (Chromium/Playwright)
npm run test:e2e       # Playwright E2E tests against a running authentik instance
```

To run a single test file:

```bash
npx vitest run path/to/file.test.ts
```

### Linting & Formatting

```bash
npm run lint           # ESLint with --fix
npm run lint-check     # ESLint, no fixes (CI mode, max-warnings: 0)
npm run lint:types     # TypeScript type checking (tsc --noEmit)
npm run prettier       # Format all files
npm run format         # Combined prettier + lint
npm run precommit      # Full pre-commit check (format, lint, types, etc.)
```

## Architecture

### Directory Structure

```
src/
  admin/        # Admin interface application
  user/         # User portal application
  flow/         # Flow execution interface + FlowExecutor
  components/   # UI components that use context (depend on app state)
  elements/     # Reusable UI elements without context (portable)
  common/       # Non-UI shared libraries (API helpers, global state, utils)
  styles/       # Global CSS (PatternFly, authentik tokens, locales)
  standalone/   # Third-party apps (loading screen, API browser)
  rac/          # Remote Access Components (Guacamole-based)
  locales/      # Auto-generated i18n (do not edit manually)

packages/
  core/         # Monorepo utilities (paths, environment, version)
  sfe/          # Standalone Frontend Engine (Rollup-based)

test/
  unit/         # Node.js unit tests (*.test.ts)
  browser/      # Playwright browser tests (*.browser.test.ts)
  lit/          # Lit test helpers (renderLit, setup.js)

e2e/            # E2E test fixtures, selectors, auth utilities
bundler/        # Custom ESBuild/Vite plugins
scripts/        # Build scripts (esbuild config, localization)
```

### Key Files

- `src/elements/Base.ts` — `AKElement`: base class for all components
- `src/elements/Interface.ts` — Base interface class with context management
- `src/common/global.ts` — Global authentik config and state
- `src/flow/FlowExecutor.ts` — Flow execution engine
- `scripts/build-web.mjs` — Main ESBuild configuration

### Conventions

- **Custom element prefix**: `ak-` (e.g., `<ak-command-palette>`)
- **Context**: Lit Context API via `ContextControllerRegistry`
- **`components/`** depends on app context; **`elements/`** must not
- **Import aliases**: `#elements/*`, `#components/*`, `#common/*`, `#admin/*`, `#user/*`, `#flow/*`, etc. (mapped in `package.json`)

## Tech Stack

| Concern            | Library                                   |
| ------------------ | ----------------------------------------- |
| UI components      | Lit 3.x + Web Components                  |
| Design system      | PatternFly 4                              |
| Build              | ESBuild + Vite 7                          |
| Tests              | Vitest 4 + Playwright                     |
| i18n               | Lit Localize (runtime mode, 18 languages) |
| API client         | `@goauthentik/api` (generated)            |
| Linting            | ESLint 9 + `@goauthentik/eslint-config`   |
| Task orchestration | Wireit                                    |

## TypeScript Notes

- `tsconfig.json` uses `"useDefineForClassFields": false` — required for Lit decorators and Storybook; do not change.
- `"moduleResolution": "bundler"` — path aliases resolved at build time via `package.json#imports`.
- Decorators are enabled with `"experimentalDecorators": true`.

## i18n

Translatable strings use `msg()` from `@lit/localize`. To add new strings, use `msg()` and run:

```bash
npm run extract-locales   # Extract new strings to XLIFF files
npm run pseudolocalize    # Generate pseudo-locales for layout testing
```

Never edit files in `src/locales/` directly — they are auto-generated.
