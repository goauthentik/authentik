# @goauthentik/oxlint-config

authentik shared [oxlint](https://oxc.rs) configuration.

## Install

```sh
npm install -D @goauthentik/oxlint-config oxlint
```

`oxlint` is a peer dependency. Node `>=24` is required (oxlint runs the `.ts` config and the JS
header plugin via Node).

## Usage

Create an `oxlint.config.ts` (oxlint auto-discovers it):

```ts
import { createOxlintConfig } from "@goauthentik/oxlint-config"

export default createOxlintConfig({
    // per-repo tweaks, e.g. ignorePatterns
})
```

### Platform layering

Files are matched by their final name segment, and cross-runtime imports are flagged via core
`no-restricted-imports`:

- `browser` → `client`, `browser`
- `node` → `server`, `node`, `sdk`
- `agnostic` → `shared`, `common`
- `worker` → `worker`

A `*-client` file importing a `*-server` package (or vice versa) is an error; `*-shared`/`*-common`
files may not import Node built-ins at all.

