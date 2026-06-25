# `@goauthentik/api` (vendored)

This directory is a **workspace-vendored copy** of the OpenAPI-generated
TypeScript client. It is consumed locally by `web/` at the placeholder
version `0.0.0` via the symlink `web/packages/client-ts → ../../packages/client-ts`.

It is **not** the package published to npm.

## Where the published package comes from

The `@goauthentik/api` package on npm is published from a separate
repository:

- **Source:** <https://github.com/goauthentik/client-ts>
- **Cadence:** one tag per authentik release; the `main` branch of that
  repo holds only the generator scaffolding, and per-version source
  lives on per-version branches/tags.

Both this directory and the standalone `client-ts` repo run
[openapi-generator-cli](https://openapi-generator.tech/) (`typescript-fetch`)
against the same `schema.yml`. They share the same generation approach
but are **separate code paths** — there is no automated mirroring.

**Implication:** structural fixes to the generated client (tsconfig
shape, package.json layout, exports map) need to land in **both**
places. The templates in `packages/client-ts/templates/` are the
source of truth for files this repo regenerates; the upstream
`client-ts` repo has its own copies.

## How regeneration works

```sh
make gen-client-ts
```

This invocation:

1. Wipes `packages/client-ts/src/`.
2. Runs `openapi-generator-cli generate -g typescript-fetch` against
   `schema.yml`, using `packages/client-ts/templates/` for any
   templated files (notably `tsconfig.mustache`, `tsconfig.esm.mustache`).
3. Runs `prettier --write` over the result.
4. Reinstalls `web/`'s `node_modules` so the symlinked workspace
   picks up the regenerated source.

`.openapi-generator-ignore` preserves the following across regeneration:

- `package.json` — so manually-curated metadata (exports map, scripts,
  `type` field) survives.
- `README.md` — this file.
- `.gitignore`, `.npmignore`, `docs/**`.

`tsconfig.json` and `tsconfig.esm.json` are **not** preserved — they are
regenerated from their `.mustache` templates each run.

## Dual-package layout (CJS + ESM)

The package ships both shapes from a single source tree:

| Path                     | Shape | Driven by                                  |
| ------------------------ | ----- | ------------------------------------------ |
| `dist/index.js`          | CJS   | `tsconfig.json` (`module: NodeNext`)       |
| `dist/esm/index.js`      | ESM   | `tsconfig.esm.json` (`module: ESNext`)     |
| `dist/esm/package.json`  | —     | `scripts/finalize-esm.mjs` (postbuild)     |

`dist/esm/package.json` contains `{ "type": "module" }` so that Node's
resolver (and any bundler that walks `package.json` chains) treats the
ESM `.js` files as ESM, regardless of the package root's
`"type": "commonjs"`.

The same postbuild script (`scripts/finalize-esm.mjs`) appends `.js`
extensions to extension-less relative specifiers in the ESM output.
The `typescript-fetch` generator emits `from "./runtime"` rather than
`from "./runtime.js"`, and TypeScript's `module: "ESNext"` emit does
not rewrite these — without the fixup Node's strict ESM resolver
throws `ERR_MODULE_NOT_FOUND`. Bundlers accept either form, so the
CJS output is left untouched.

Consumer-facing entry points are declared via the `exports` conditional
map in `package.json`:

- `types` → `./dist/index.d.ts`
- `import` → `./dist/esm/index.js`
- `require` / `default` → `./dist/index.js`

The legacy `main` / `module` fields are kept for resolvers that don't
honor `exports`.

## Local development

```sh
# Rebuild after editing src/ or templates/
npm --prefix packages/client-ts run build

# Regenerate src/ from schema.yml (then rebuild)
make gen-client-ts
```

`web/`'s vite/esbuild stack consumes the artifacts under
`packages/client-ts/dist/` via the workspace symlink. After rebuilding
the client, restart any running dev server so it picks up the fresh
output.
