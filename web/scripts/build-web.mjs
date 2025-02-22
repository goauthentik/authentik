import { execFileSync } from "child_process";
import esbuild from "esbuild";
import findFreePorts from "find-free-ports";
import { copyFileSync, mkdirSync, readFileSync, statSync } from "fs";
import { globSync } from "glob";
import * as path from "path";
import { cwd } from "process";
import process from "process";
import { fileURLToPath } from "url";

import { mdxPlugin } from "./esbuild/build-mdx-plugin.mjs";
import { buildObserverPlugin } from "./esbuild/build-observer-plugin.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
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
 * @typedef {[source: string, destination: string]} EntryPoint
 */

/**
 * This starts the definitions used for esbuild: Our targets, our arguments, the function for
 * running a build, and three options for building: watching, building, and building the proxy.
 * Ordered by largest to smallest interface to build even faster
 *
 * @type {EntryPoint[]}
 */
const entryPoints = [
    ["admin/AdminInterface/AdminInterface.ts", "admin"],
    ["user/UserInterface.ts", "user"],
    ["flow/FlowInterface.ts", "flow"],
    ["standalone/api-browser/index.ts", "standalone/api-browser"],
    ["rac/index.ts", "rac"],
    ["standalone/loading/index.ts", "standalone/loading"],
    ["polyfill/poly.ts", "."],
];

/**
 * @satisfies {import("esbuild").BuildOptions}
 */
const BASE_ESBUILD_OPTIONS = {
    bundle: true,
    write: true,
    sourcemap: true,
    minify: NODE_ENV === "production",
    splitting: true,
    treeShaking: true,
    external: ["*.woff", "*.woff2"],
    tsconfig: "./tsconfig.json",
    loader: {
        ".css": "text",
        ".md": "text",
    },
    define: definitions,
    format: "esm",
    plugins: [mdxPlugin()],
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

/**
 * Build a single entry point.
 *
 * @param {EntryPoint} buildTarget
 * @param {Partial<esbuild.BuildOptions>} [overrides]
 * @throws {Error} on build failure
 */
function createEntryPointOptions([source, dest], overrides = {}) {
    const outdir = path.join(__dirname, "..", "dist", dest);

    return {
        ...BASE_ESBUILD_OPTIONS,
        entryPoints: [`./src/${source}`],
        entryNames: `[dir]/[name]-${composeVersionID()}`,
        outdir,
        ...overrides,
    };
}

/**
 * Build all entry points in parallel.
 *
 * @param {EntryPoint[]} entryPoints
 */
async function buildParallel(entryPoints) {
    await Promise.allSettled(
        entryPoints.map((entryPoint) => {
            return esbuild.build(createEntryPointOptions(entryPoint));
        }),
    );
}

function doHelp() {
    console.log(`Build the authentik UI

        options:
            -w, --watch: Build all ${entryPoints.length} interfaces
            -p, --proxy: Build only the polyfills and the loading application
            -h, --help: This help message
`);

    process.exit(0);
}

async function doWatch() {
    console.log("Watching all entry points...");

    const wathcherPorts = await findFreePorts(entryPoints.length);

    const buildContexts = await Promise.all(
        entryPoints.map((entryPoint, i) => {
            const port = wathcherPorts[i];
            const serverURL = new URL(`http://localhost:${port}/events`);

            return esbuild.context(
                createEntryPointOptions(entryPoint, {
                    plugins: [
                        ...BASE_ESBUILD_OPTIONS.plugins,
                        buildObserverPlugin({
                            serverURL,
                            logPrefix: entryPoint[1],
                            relativeRoot: path.join(__dirname, ".."),
                        }),
                    ],
                    define: {
                        ...definitions,
                        "process.env.WATCHER_URL": JSON.stringify(serverURL.toString()),
                    },
                }),
            );
        }),
    );

    await Promise.all(buildContexts.map((context) => context.rebuild()));

    await Promise.allSettled(buildContexts.map((context) => context.watch()));

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

    return buildParallel(entryPoints);
}

async function doProxy() {
    return buildParallel(
        entryPoints.filter(([_, dest]) => ["standalone/loading", "."].includes(dest)),
    );
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
