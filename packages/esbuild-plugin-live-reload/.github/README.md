_An ESBuild development plugin that watches for file changes and triggers automatic browser refreshes._

## Quick start

```sh
npm install -D @goauthentik/esbuild-plugin-live-reload
# Or with Yarn:
yarn add -D @goauthentik/esbuild-plugin-live-reload
```

### 1. Configure ESBuild

```js
import { liveReloadPlugin } from "@goauthentik/esbuild-plugin-live-reload";

import esbuild from "esbuild";

const NodeEnvironment = process.env.NODE_ENV || "development";

/**
 * @type {esbuild.BuildOptions}
 */
const buildOptions = {
    // ... Your build options.
    define: {
        "process.env.NODE_ENV": JSON.stringify(NodeEnvironment),
    },
    plugins: [
        /** @see {@link LiveReloadPluginOptions} */
        liveReloadPlugin(),
    ],
};

const buildContext = await esbuild.context(buildOptions);

await buildContext.rebuild();
await buildContext.watch();
```

### 2. Connect your browser

Add the following import near the beginning of your application's entry point.

```js
if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}
```

That's it! Your browser will now automatically refresh whenever ESBuild finishes rebuilding your code.

## About authentik

[authentik](https://goauthentik.io) is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and Auth0.

We built this plugin to streamline our development workflow, and we're sharing it with the community. If you have any questions, feature requests, or bug reports, please [open an issue](https://github.com/goauthentik/authentik/issues/new/choose).

## License

This code is licensed under the [MIT License](https://www.tldrlegal.com/license/mit-license)
