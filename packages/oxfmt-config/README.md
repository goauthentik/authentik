# @goauthentik/oxfmt-config

authentik's shared [oxfmt](https://oxc.rs) formatter configuration.

Replaces `@goauthentik/prettier-config`. oxfmt covers natively what previously needed three
Prettier plugins: import organization, JSDoc formatting, and `package.json` key ordering.

## Install

```sh
npm install -D @goauthentik/oxfmt-config oxfmt
```

`oxfmt` is a peer dependency.

## Usage

oxfmt has no `extends`, so spread the config into your own `oxfmt.config.ts` (oxfmt auto-discovers
it):

```ts
import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config"

export default {
	...authentikOxfmtConfig,
	// per-repo tweaks, e.g. ignorePatterns
}
```
