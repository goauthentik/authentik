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
