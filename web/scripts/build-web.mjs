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
import { styleLoaderPlugin } from "#bundler/style-loader-plugin/node";
import { createBundleDefinitions } from "#bundler/utils/node";
import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

import { NodeEnvironment } from "@goauthentik/core/environment/node";
import { MonoRepoRoot } from "@goauthentik/core/paths/node";
import { BuildIdentifier } from "@goauthentik/core/version/node";

import { deepmerge } from "deepmerge-ts";
import esbuild from "esbuild";

/// <reference types="../types/esbuild.js" />

const logger = ConsoleLogger.child({ name: "Build" });

const bundleDefinitions = createBundleDefinitions();

const publicBundledDefinitions = Object.fromEntries(
    Object.entries(bundleDefinitions).map(([name, value]) => [name, JSON.parse(value)]),
);
logger.info(publicBundledDefinitions, "Bundle definitions");

/**
 * @typedef {[from: string, to: string]} SourceDestinationPair
 */

/**
 * @type {SourceDestinationPair[]}
 */
const assets = [
    [
        path.join(path.dirname(EntryPoint.StandaloneLoading.in), "startup"),
        path.dirname(EntryPoint.StandaloneLoading.out),
    ],
    [path.resolve(PackageRoot, "src", "assets", "images"), "./assets/images"],
    [path.resolve(PackageRoot, "icons"), "./assets/icons"],
];

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
    color: !process.env.NO_COLOR,
    treeShaking: true,
    tsconfig: path.resolve(PackageRoot, "tsconfig.build.json"),
    loader: {
        ".css": "text",
        ".woff": "file",
        ".woff2": "file",
        ".jpg": "file",
        ".png": "file",
        ".svg": "text",
    },
    plugins: [
        {
            name: "copy",
            setup(build) {
                build.onEnd(async () => {
                    /**
                     * @type {import('esbuild').PartialMessage[]}
                     */
                    const errors = [];

                    /**
                     * @param {SourceDestinationPair} pair
                     */
                    const copy = ([from, to]) => {
                        const resolvedDestination = path.resolve(DistDirectory, to);

                        logger.debug(`📋 Copying assets from ${from} to ${to}`);

                        return fs
                            .cp(from, resolvedDestination, { recursive: true })
                            .catch((error) => {
                                errors.push({
                                    text: `Failed to copy assets from ${from} to ${to}: ${error}`,
                                    location: {
                                        file: from,
                                    },
                                });
                            });
                    };

                    await Promise.all(assets.map(copy));

                    return { errors };
                });
            },
        },

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

/**
 *
 * @returns {Promise<() => Promise<void>>} dispose
 */
async function doWatch() {
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
        plugins: [...developmentPlugins, styleLoaderPlugin({ logger, watch: true })],
    });

    const buildContext = await esbuild.context(buildOptions);

    await buildContext.watch();

    const httpURL = new URL("http://localhost");
    httpURL.port = process.env.COMPOSE_PORT_HTTP ?? "9000";

    const httpsURL = new URL("https://localhost");
    httpsURL.port = process.env.COMPOSE_PORT_HTTPS ?? "9443";

    logger.info(`🚀 Server running`);

    logger.info(`🔓 ${httpURL.href}`);
    logger.info(`🔒 ${httpsURL.href}`);

    return () => {
        logger.flush();
        console.info("");
        console.info("🛑 Stopping file watcher...");

        return buildContext.dispose();
    };
}

async function doBuild() {
    logger.info(`🤖 Building entry points:\n\t${Object.keys(EntryPoint).join("\n\t")}`);

    const entryPoints = Object.values(EntryPoint);

    const buildOptions = createESBuildOptions({
        entryPoints,
        plugins: [styleLoaderPlugin({ logger })],
    });

    await esbuild.build(buildOptions);

    logger.info("Build complete");
}

async function doProxy() {
    const entryPoints = [EntryPoint.InterfaceStyles, EntryPoint.StaticStyles];

    const buildOptions = createESBuildOptions({
        entryPoints,
        plugins: [styleLoaderPlugin({ logger })],
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
            .then((dispose) => {
                if (!dispose) {
                    process.exit(0);
                }

                /**
                 * @type {Promise<void>}
                 */
                const signalListener = new Promise((resolve) => {
                    // We prevent multiple attempts to dispose the context
                    // because ESBuild will repeatedly restart its internal clean-up logic.
                    // However, sending a second SIGINT will still exit the process immediately.
                    let signalCount = 0;

                    process.on("SIGINT", () => {
                        if (signalCount > 3) {
                            // Something is taking too long and the user wants to exit now.
                            console.log("🛑 Forcing exit...");
                            process.exit(0);
                        }
                    });

                    process.once("SIGINT", () => {
                        signalCount++;

                        dispose().finally(() => {
                            console.log("✅ Done!");

                            resolve();
                        });
                    });

                    logger.info("🚪 Press Ctrl+C to exit.");
                });

                return signalListener;
            })
            .then(() => process.exit(0))
            .catch(() => process.exit(1)),
    );
