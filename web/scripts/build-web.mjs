/**
 * @file ESBuild script for building the authentik web UI.
 *
 * @import { BuildOptions } from "esbuild";
 */
import {
    MonoRepoRoot,
    NodeEnvironment,
    readBuildIdentifier,
    resolvePackage,
    serializeEnvironmentVars,
} from "@goauthentik/monorepo";
import { DistDirectory, DistDirectoryName, EntryPoint, PackageRoot } from "@goauthentik/web/paths";
import { deepmerge } from "deepmerge-ts";
import esbuild from "esbuild";
import copy from "esbuild-plugin-copy";
import { polyfillNode } from "esbuild-plugin-polyfill-node";
import findFreePorts from "find-free-ports";
import * as path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { mdxPlugin } from "./esbuild/build-mdx-plugin.mjs";
import { buildObserverPlugin } from "./esbuild/build-observer-plugin.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const definitions = serializeEnvironmentVars({
    NODE_ENV: NodeEnvironment,
    CWD: process.cwd(),
    AK_API_BASE_PATH: process.env.AK_API_BASE_PATH,
    WATCHER_URL: process.env.WATCHER_URL,
});

const patternflyPath = resolvePackage("@patternfly/patternfly");

/**
 * @type {Readonly<BuildOptions>}
 */
const BASE_ESBUILD_OPTIONS = {
    entryNames: `[dir]/[name]-${readBuildIdentifier()}`,
    chunkNames: "[dir]/chunks/[name]-[hash]",
    assetNames: "assets/[dir]/[name]-[hash]",
    publicPath: path.join("/static", DistDirectoryName),
    outdir: DistDirectory,
    bundle: true,
    write: true,
    sourcemap: true,
    minify: NodeEnvironment === "production",
    legalComments: "external",
    splitting: true,
    treeShaking: true,
    external: ["*.woff", "*.woff2"],
    tsconfig: path.resolve(PackageRoot, "tsconfig.build.json"),
    loader: {
        ".css": "text",
    },
    plugins: [
        copy({
            assets: [
                {
                    from: path.join(patternflyPath, "patternfly.min.css"),
                    to: ".",
                },
                {
                    from: path.join(patternflyPath, "assets", "**"),
                    to: "./assets",
                },
                {
                    from: path.resolve(PackageRoot, "src", "common", "styles", "**"),
                    to: ".",
                },
                {
                    from: path.resolve(PackageRoot, "src", "assets", "images", "**"),
                    to: "./assets/images",
                },
                {
                    from: path.resolve(PackageRoot, "icons", "*"),
                    to: "./assets/icons",
                },
            ],
        }),
        polyfillNode({
            polyfills: {
                path: true,
            },
        }),
        mdxPlugin({
            root: MonoRepoRoot,
        }),
    ],
    define: definitions,
    format: "esm",
    logOverride: {
        /**
         * HACK: Silences issue originating in ESBuild.
         *
         * @see {@link https://github.com/evanw/esbuild/blob/b914dd30294346aa15fcc04278f4b4b51b8b43b5/internal/logger/msg_ids.go#L211 ESBuild source}
         * @expires 2025-08-11
         */
        "invalid-source-url": "silent",
    },
};

/**
 * Creates an ESBuild options, extending the base options with the given overrides.
 *
 * @param {BuildOptions} overrides
 * @returns {BuildOptions}
 */
export function createESBuildOptions(overrides) {
    /**
     * @type {BuildOptions}
     */
    const mergedOptions = deepmerge(BASE_ESBUILD_OPTIONS, overrides);

    return mergedOptions;
}

function doHelp() {
    console.log(`Build the authentik UI

        options:
            -w, --watch: Build all interfaces
            -p, --proxy: Build only the polyfills and the loading application
            -h, --help: This help message
`);

    process.exit(0);
}

async function doWatch() {
    console.log("Watching all entry points...");

    const wathcherPorts = await findFreePorts(1);
    const port = wathcherPorts[0];
    const serverURL = new URL(`http://localhost:${port}/events`);

    const entryPoints = Object.values(EntryPoint);

    const buildOptions = createESBuildOptions({
        entryPoints,
        plugins: [
            buildObserverPlugin({
                serverURL,
                relativeRoot: path.join(__dirname, ".."),
            }),
        ],
        define: serializeEnvironmentVars({
            WATCHER_URL: serverURL.toString(),
        }),
    });

    const buildContext = await esbuild.context(buildOptions);

    await buildContext.rebuild();
    await buildContext.watch();

    return /** @type {Promise<void>} */ (
        new Promise((resolve) => {
            process.on("SIGINT", () => {
                resolve();
            });
        })
    );
}

async function doBuild() {
    console.log("Building all entry points");

    const entryPoints = Object.values(EntryPoint);

    const buildOptions = createESBuildOptions({
        entryPoints,
    });

    await esbuild.build(buildOptions);

    console.log("Build complete");
}

async function doProxy() {
    const entryPoints = [EntryPoint.StandaloneLoading];

    const buildOptions = createESBuildOptions({
        entryPoints,
    });

    await esbuild.build(buildOptions);
    console.log("Proxy build complete");
}

async function delegateCommand() {
    const command = process.argv[2];

    switch (command) {
        case "-h":
        case "--help":
            return doHelp();
        case "-w":
        case "--watch":
            return doWatch();
        // There's no watch-for-proxy, sorry.
        case "-p":
        case "--proxy":
            return doProxy();
        default:
            return doBuild();
    }
}

await delegateCommand()
    .then(() => {
        console.log("Build complete");
        process.exit(0);
    })
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
