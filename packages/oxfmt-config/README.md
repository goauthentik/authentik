# @goauthentik/oxfmt-config

authentik's shared [oxfmt](https://oxc.rs) formatter configuration.

## Install

```sh
npm install -D @goauthentik/oxfmt-config oxfmt
```

`oxfmt` is a peer dependency.

## Usage

oxfmt has no `extends`, so build the config in your own `oxfmt.config.ts` (oxfmt auto-discovers
it):

```ts
import { createOxfmtConfig } from "@goauthentik/oxfmt-config";

export default createOxfmtConfig();
```

`createOxfmtConfig` takes the same shape of options as `createOxlintConfig` in
`@goauthentik/oxlint-config`:

```ts
import { createOxfmtConfig, DefaultIgnorePatterns } from "@goauthentik/oxfmt-config";

export default createOxfmtConfig({
    ignorePatterns: [...DefaultIgnorePatterns, "fixtures/**"],
    // `overrides.overrides` appends to the shared per-file overrides; every other
    // key replaces its base counterpart.
    overrides: { printWidth: 120 },
});
```

`authentikOxfmtConfig` is still exported for callers that want the raw object.
