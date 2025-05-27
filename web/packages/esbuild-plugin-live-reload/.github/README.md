# `@goauthentik/esbuild-plugin-live-reload`

_A plugin that enables live reloading of ESBuild during development._

## Usage

### Node.js setup

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
    plugins: [liveReloadPlugin(/** @see {@link LiveReloadPluginOptions} */)],
};

const buildContext = await esbuild.context(buildOptions);

await buildContext.rebuild();
await buildContext.watch();
```

### Browser setup

```js
// Place this at the beginning of your application's entry point.

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}
```

## About authentik

[authentik](https://goauthentik.io) is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and Auth0.

We use this package to enable live reloading of ESBuild during development, and we hope you'll find it useful too. If you have any questions, feature requests, or bug reports, please [open an issue](https://github.com/goauthentik/authentik/issues/new/choose).

## License

This code is licensed under the [MIT License](https://www.tldrlegal.com/license/mit-license).
[A copy of the license](./LICENSE.txt) is included with this package.
