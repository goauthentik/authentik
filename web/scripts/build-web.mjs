/**
 * @file ESBuild script for building the authentik web UI.
 */

import "@goauthentik/core/environment/load/node";

import { existsSync } from "node:fs";
import * as fs from "node:fs/promises";
import { createRequire } from "node:module";
import * as path from "node:path";

import { copyAssets } from "./build-assets.mjs";

/**
 * @file ESBuild script for building the authentik web UI.
 *
 * @import { BuildOptions, Plugin } from "esbuild";
 */
import { mdxPlugin } from "#bundler/mdx-plugin/node";
import { styleLoaderPlugin } from "#bundler/style-loader-plugin/node";
import { createBundleDefinitions } from "#bundler/utils/node";
import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

import { NodeEnvironment } from "@goauthentik/core/environment/node";
import { MonoRepoRoot } from "@goauthentik/core/paths/node";
import { BuildIdentifier } from "@goauthentik/core/version/node";

import esbuild from "esbuild";

/// <reference types="../types/esbuild.js" />

const logger = ConsoleLogger.child({ name: "Build" });

const bundleDefinitions = createBundleDefinitions();

const publicBundledDefinitions = Object.fromEntries(
    Object.entries(bundleDefinitions).map(([name, value]) => [name, JSON.parse(value)]),
);
logger.info(publicBundledDefinitions, "Bundle definitions");

const entryPointNames = Object.keys(EntryPoint);
const entryPoints = Object.values(EntryPoint);
const entryPointsDescription = entryPointNames.join("\n\t");

/**
 * @type {Plugin[]}
 */
const BASE_ESBUILD_PLUGINS = [
    {
        name: "copy",
        setup(build) {
            build.onEnd(async () => {
                /**
                 * @type {import('esbuild').PartialMessage[]}
                 */
                const errors = [];

                await copyAssets();

                return { errors };
            });
        },
    },

    mdxPlugin({
        root: MonoRepoRoot,
    }),
];

/**
 * Packages whose copy must be forced to resolve to this workspace's own install, mirroring
 * `web/vite.config.js`'s `resolve.dedupe`.
 *
 * `packages/lit-jsx/dist` (and `packages/truncator`) depend on `lit` themselves, so without this
 * an entry point can end up bundling two separate copies of the same Lit version, which Lit
 * detects at runtime and warns about (and which can also silently break custom element
 * registration).
 *
 * @type {ReadonlyArray<string>}
 */
const LIT_DEDUPE_PACKAGES = ["lit", "lit-html", "lit-element", "@lit/reactive-element"];

const nodeRequire = createRequire(import.meta.url);

/**
 * Resolve a bare package name to the absolute directory of the copy Node's resolution algorithm
 * would find first.
 *
 * This intentionally doesn't use `resolvePackage()` from `@goauthentik/core/paths/node`: that
 * helper resolves via the package's `./package.json` export, but none of the `LIT_DEDUPE_PACKAGES`
 * expose that subpath in their `exports` map. Instead, this walks the same `node_modules` lookup
 * order Node would use (`require.resolve.paths`) and takes the first directory that actually
 * contains the package.
 *
 * @param {string} packageName
 * @returns {string}
 */
function resolvePackageDirectory(packageName) {
    const candidateRoots = nodeRequire.resolve.paths(packageName) ?? [];

    for (const root of candidateRoots) {
        const candidate = path.join(root, packageName);

        if (existsSync(path.join(candidate, "package.json"))) {
            return candidate;
        }
    }

    throw new Error(`🚫 Failed to resolve package "${packageName}"`);
}

/**
 * Force a single copy so Lit doesn't warn about (or break on) duplicate versions in the
 * production bundle.
 *
 * @see web/vite.config.js's `resolve.dedupe` for the Vite dev/test equivalent.
 *
 * @type {Record<string, string>}
 */
const litDedupeAlias = Object.fromEntries(
    LIT_DEDUPE_PACKAGES.map((packageName) => [packageName, resolvePackageDirectory(packageName)]),
);

/**
 * @type {BuildOptions}
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
        ".svg": "file",
    },
    /**
     * Conditions for module resolution.
     *
     * @see https://esbuild.github.io/api/#conditions
     * @see https://nodejs.org/api/packages.html#packages_conditional_exports
     */
    conditions: NodeEnvironment === "production" ? ["production"] : ["development", "production"],
    alias: litDedupeAlias,
    plugins: BASE_ESBUILD_PLUGINS,
    define: bundleDefinitions,
    format: "esm",
};

/**
 * Creates an ESBuild options, extending the base options with the given overrides.
 *
 * @param {BuildOptions["entryPoints"]} entryPoints
 * @param {Plugin[]} plugIns
 * @returns {BuildOptions}
 */
export function createESBuildOptions(entryPoints, plugIns = []) {
    const plugins = [...BASE_ESBUILD_PLUGINS, ...plugIns];

    return {
        ...BASE_ESBUILD_OPTIONS,
        entryPoints,
        plugins,
    };
}

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

function doHelp() {
    logger.info(`Build the authentik UI

        options:
            -w, --watch: Build all interfaces
            -s, --styles-only: Build the static CSS`);

    process.exit(0);
}

/**
 *
 * @returns {Promise<() => Promise<void>>} dispose
 */
async function doWatch() {
    logger.info(`🤖 Watching entry points:\n\t${entryPointsDescription}`);

    const developmentPlugins = await import("@goauthentik/esbuild-plugin-live-reload/plugin")
        .then(({ liveReloadPlugin }) => [
            liveReloadPlugin({
                relativeRoot: PackageRoot,
                logger: logger.child({
                    name: "Live Reload",
                }),
            }),
        ])
        .catch(() => []);

    const buildOptions = createESBuildOptions(entryPoints, [
        ...developmentPlugins,
        styleLoaderPlugin({ logger, watch: true }),
    ]);

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
    logger.info(`🤖 Building entry points:\n\t${entryPointsDescription}`);

    const buildOptions = createESBuildOptions(entryPoints, [styleLoaderPlugin({ logger })]);

    await esbuild.build(buildOptions);

    logger.info("Build complete");
}

async function doProxy() {
    const entryPoints = [
        EntryPoint.InterfaceStyles,
        EntryPoint.StaticStyles,
        EntryPoint.FlowStyles,
    ];
    const buildOptions = createESBuildOptions(entryPoints, [styleLoaderPlugin({ logger })]);

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
        case "-s":
        case "--styles-only":
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
