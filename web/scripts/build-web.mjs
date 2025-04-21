/**
 * @file ESBuild script for building the authentik web UI.
 *
 * @import { BuildOptions } from "esbuild";
 */
import { liveReloadPlugin } from "@goauthentik/esbuild-plugin-live-reload/plugin";
import { DistDirectory, DistDirectoryName, EntryPoint, PackageRoot } from "@goauthentik/web/paths";
import { deepmerge } from "deepmerge-ts";
import esbuild from "esbuild";
import { polyfillNode } from "esbuild-plugin-polyfill-node";
import { globSync } from "glob";
import { execFileSync } from "node:child_process";
import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import process, { cwd } from "node:process";

import { mdxPlugin } from "./esbuild/build-mdx-plugin.mjs";

const logPrefix = "[Build]";

let authentikProjectRoot = path.join(__dirname, "..", "..");

try {
    // Use the package.json file in the root folder, as it has the current version information.
    authentikProjectRoot = execFileSync("git", ["rev-parse", "--show-toplevel"], {
        encoding: "utf8",
    }).replace("\n", "");
} catch (_error) {
    // We probably don't have a .git folder, which could happen in container builds.
}

const packageJSONPath = path.join(authentikProjectRoot, "./package.json");
const rootPackage = JSON.parse(readFileSync(packageJSONPath, "utf8"));

const NODE_ENV = process.env.NODE_ENV || "development";
const AK_API_BASE_PATH = process.env.AK_API_BASE_PATH || "";

const environmentVars = new Map([
    ["NODE_ENV", NODE_ENV],
    ["CWD", cwd()],
    ["AK_API_BASE_PATH", AK_API_BASE_PATH],
]);

const definitions = Object.fromEntries(
    Array.from(environmentVars).map(([key, value]) => {
        return [`process.env.${key}`, JSON.stringify(value)];
    }),
);
/**
 * All is magic is just to make sure the assets are copied into the right places. This is a very
 * stripped down version of what the rollup-copy-plugin does, without any of the features we don't
 * use, and using globSync instead of globby since we already had globSync lying around thanks to
 * Typescript. If there's a third argument in an array entry, it's used to replace the internal path
 * before concatenating it all together as the destination target.
 * @type {Array<[string, string, string?]>}
 */
const assetsFileMappings = [
    ["node_modules/@patternfly/patternfly/patternfly.min.css", "."],
    ["node_modules/@patternfly/patternfly/assets/**", ".", "node_modules/@patternfly/patternfly/"],
    ["src/common/styles/**", "."],
    ["src/assets/images/**", "./assets/images"],
    ["./icons/*", "./assets/icons"],
];

/**
 * @param {string} filePath
 */
const isFile = (filePath) => statSync(filePath).isFile();

/**
 * @param {string} src Source file
 * @param {string} dest Destination folder
 * @param {string} [strip] Path to strip from the source file
 */
function nameCopyTarget(src, dest, strip) {
    const target = path.join(dest, strip ? src.replace(strip, "") : path.parse(src).base);
    return [src, target];
}

for (const [source, rawdest, strip] of assetsFileMappings) {
    const matchedPaths = globSync(source);
    const dest = path.join("dist", rawdest);

    const copyTargets = matchedPaths.map((path) => nameCopyTarget(path, dest, strip));

    for (const [src, dest] of copyTargets) {
        if (isFile(src)) {
            mkdirSync(path.dirname(dest), { recursive: true });
            copyFileSync(src, dest);
        }
    }
}

/**
 * @type {Readonly<BuildOptions>}
 */
const BASE_ESBUILD_OPTIONS = {
    entryNames: `[dir]/[name]-${composeVersionID()}`,
    chunkNames: "[dir]/chunks/[name]-[hash]",
    assetNames: "assets/[dir]/[name]-[hash]",
    publicPath: path.join("/static", DistDirectoryName),
    outdir: DistDirectory,
    bundle: true,
    write: true,
    sourcemap: true,
    minify: NODE_ENV === "production",
    legalComments: "external",
    splitting: true,
    treeShaking: true,
    external: ["*.woff", "*.woff2"],
    tsconfig: path.resolve(PackageRoot, "tsconfig.build.json"),
    loader: {
        ".css": "text",
    },
    plugins: [
        polyfillNode({
            polyfills: {
                path: true,
            },
        }),
        mdxPlugin({
            root: authentikProjectRoot,
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
 * Creates a version ID for the build.
 * @returns {string}
 */
function composeVersionID() {
    const { version } = rootPackage;
    const buildHash = process.env.GIT_BUILD_HASH;

    if (buildHash) {
        return `${version}+${buildHash}`;
    }

    return version;
}

async function cleanDistDirectory() {
    const timerLabel = `${logPrefix} ♻️ Cleaning previous builds...`;

    console.time(timerLabel);

    await fs.rm(DistDirectory, {
        recursive: true,
        force: true,
    });

    await fs.mkdir(DistDirectory, {
        recursive: true,
    });

    console.timeEnd(timerLabel);
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
    console.log(`Build the authentik UI

        options:
            -w, --watch: Build all interfaces
            -p, --proxy: Build only the polyfills and the loading application
            -h, --help: This help message
`);

    process.exit(0);
}

async function doWatch() {
    console.group(`${logPrefix} 🤖 Watching entry points`);

    const entryPoints = Object.entries(EntryPoint).map(([entrypointID, target]) => {
        console.log(entrypointID);

        return target;
    });

    console.groupEnd();

    const buildOptions = createESBuildOptions({
        entryPoints,
        plugins: [
            liveReloadPlugin({
                relativeRoot: PackageRoot,
            }),
        ],
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
    console.group(`${logPrefix} 🚀 Building entry points:`);

    const entryPoints = Object.entries(EntryPoint).map(([entrypointID, target]) => {
        console.log(entrypointID);

        return target;
    });

    console.groupEnd();

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

await cleanDistDirectory()
    // ---
    .then(() =>
        delegateCommand()
            .then(() => {
                console.log("Build complete");
                process.exit(0);
            })
            .catch((error) => {
                console.error(error);
                process.exit(1);
            }),
    );
