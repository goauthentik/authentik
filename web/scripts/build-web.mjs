/**
 * @file ESBuild script for building the authentik web UI.
 */

import "@goauthentik/core/environment/load/node";

import * as fs from "node:fs/promises";
import * as path from "node:path";

/**
 * @file ESBuild script for building the authentik web UI.
 *
 * @import { BuildOptions } from "esbuild";
 */
import { mdxPlugin } from "#bundler/mdx-plugin/node";
import { createBundleDefinitions } from "#bundler/utils/node";
import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

import { NodeEnvironment } from "@goauthentik/core/environment/node";
import { MonoRepoRoot, resolvePackage } from "@goauthentik/core/paths/node";
import { BuildIdentifier } from "@goauthentik/core/version/node";

import { deepmerge } from "deepmerge-ts";
import esbuild from "esbuild";
import { copy } from "esbuild-plugin-copy";

/// <reference types="../types/esbuild.js" />

const logger = ConsoleLogger.child({ name: "Build" });

const bundleDefinitions = createBundleDefinitions();

const publicBundledDefinitions = Object.fromEntries(
    Object.entries(bundleDefinitions).map(([name, value]) => [name, JSON.parse(value)]),
);
logger.info(publicBundledDefinitions, "Bundle definitions");

const patternflyPath = resolvePackage("@patternfly/patternfly", import.meta);

/**
 * @type {Readonly<BuildOptions>}
 */
const BASE_ESBUILD_OPTIONS = {
    entryNames: `[dir]/[name]-${BuildIdentifier}`,
    chunkNames: "[dir]/chunks/[hash]",
    assetNames: "assets/[dir]/[name]-[hash]",
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
                    from: path.join(path.dirname(EntryPoint.StandaloneLoading.in), "startup", "**"),
                    to: path.dirname(EntryPoint.StandaloneLoading.out),
                },

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
        mdxPlugin({
            root: MonoRepoRoot,
        }),
    ],
    define: bundleDefinitions,
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

async function cleanDistDirectory() {
    logger.info(`♻️ Cleaning previous builds...`);

    await fs.rm(DistDirectory, {
        recursive: true,
        force: true,
    });

    await fs.mkdir(DistDirectory, {
        recursive: true,
    });

    logger.info(`♻️ Done!`);
}

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
    logger.info(`Build the authentik UI

        options:
            -w, --watch: Build all interfaces
            -p, --proxy: Build only the polyfills and the loading application
            -h, --help: This help message
`);

    process.exit(0);
}

async function doWatch() {
    const { promise, resolve, reject } = Promise.withResolvers();

    logger.info(`🤖 Watching entry points:\n\t${Object.keys(EntryPoint).join("\n\t")}`);

    const entryPoints = Object.values(EntryPoint);

    const developmentPlugins = await import("@goauthentik/esbuild-plugin-live-reload/plugin")
        .then(({ liveReloadPlugin }) => [
            liveReloadPlugin({
                relativeRoot: PackageRoot,
                logger: logger.child({ name: "Live Reload" }),
            }),
        ])
        .catch(() => []);

    const buildOptions = createESBuildOptions({
        entryPoints,
        plugins: developmentPlugins,
    });

    const buildContext = await esbuild.context(buildOptions);

    await buildContext.rebuild();
    await buildContext.watch();

    const httpURL = new URL("http://localhost");
    httpURL.port = process.env.COMPOSE_PORT_HTTP ?? "9000";

    const httpsURL = new URL("https://localhost");
    httpsURL.port = process.env.COMPOSE_PORT_HTTPS ?? "9443";

    logger.info(`🚀 Server running`);

    logger.info(`🔓 ${httpURL.href}`);
    logger.info(`🔒 ${httpsURL.href}`);

    let disposing = false;

    const delegateShutdown = () => {
        logger.flush();
        console.log("");

        // We prevent multiple attempts to dispose the context
        // because ESBuild will repeatedly restart its internal clean-up logic.
        // However, sending a second SIGINT will still exit the process immediately.
        if (disposing) return;

        disposing = true;

        return buildContext.dispose().then(resolve).catch(reject);
    };

    process.on("SIGINT", delegateShutdown);

    return promise;
}

async function doBuild() {
    logger.info(`🤖 Watching entry points:\n\t${Object.keys(EntryPoint).join("\n\t")}`);

    const entryPoints = Object.values(EntryPoint);

    const buildOptions = createESBuildOptions({
        entryPoints,
    });

    await esbuild.build(buildOptions);

    logger.info("Build complete");
}

async function doProxy() {
    const entryPoints = [EntryPoint.StandaloneLoading];

    const buildOptions = createESBuildOptions({
        entryPoints,
    });

    await esbuild.build(buildOptions);
    logger.info("Proxy build complete");
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

await cleanDistDirectory()
    // ---
    .then(() =>
        delegateCommand()
            .then(() => {
                process.exit(0);
            })
            .catch((error) => {
                logger.error(error);
                process.exit(1);
            }),
    );
