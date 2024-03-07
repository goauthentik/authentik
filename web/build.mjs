import * as chokidar from "chokidar";
import esbuild from "esbuild";
import fs from "fs";
import { globSync } from "glob";
import path from "path";
import { cwd } from "process";
import process from "process";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

// eslint-disable-next-line no-undef
const isProdBuild = process.env.NODE_ENV === "production";

// eslint-disable-next-line no-undef
const apiBasePath = process.env.AK_API_BASE_PATH || "";

const definitions = {
    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
    "process.env.CWD": JSON.stringify(cwd()),
    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
};

// All is magic is just to make sure the assets are copied into the right places. This is a very stripped down version
// of what the rollup-copy-plugin does, without any of the features we don't use, and using globSync instead of globby
// since we already had globSync lying around thanks to Typescript. If there's a third argument in an array entry, it's
// used to replace the internal path before concatenating it all together as the destination target.

const otherFiles = [
    ["node_modules/@patternfly/patternfly/patternfly.min.css", "."],
    ["node_modules/@patternfly/patternfly/assets/**", ".", "node_modules/@patternfly/patternfly/"],
    ["src/custom.css", "."],
    ["src/common/styles/**", "."],
    ["src/assets/images/**", "./assets/images"],
    ["./icons/*", "./assets/icons"],
];

const isFile = (filePath) => fs.statSync(filePath).isFile();
function nameCopyTarget(src, dest, strip) {
    const target = path.join(dest, strip ? src.replace(strip, "") : path.parse(src).base);
    return [src, target];
}

for (const [source, rawdest, strip] of otherFiles) {
    const matchedPaths = globSync(source);
    const dest = path.join("dist", rawdest);
    const copyTargets = matchedPaths.map((path) => nameCopyTarget(path, dest, strip));
    for (const [src, dest] of copyTargets) {
        if (isFile(src)) {
            fs.mkdirSync(path.dirname(dest), { recursive: true });
            fs.copyFileSync(src, dest);
        }
    }
}

// This starts the definitions used for esbuild: Our targets, our arguments, the function for running a build, and three
// options for building: watching, building, and building the proxy.

const interfaces = [
    ["polyfill/poly.ts", "."],
    ["standalone/loading/index.ts", "standalone/loading"],
    ["flow/FlowInterface.ts", "flow"],
    ["user/UserInterface.ts", "user"],
    ["enterprise/rac/index.ts", "enterprise/rac"],
    ["standalone/api-browser/index.ts", "standalone/api-browser"],
    ["admin/AdminInterface/AdminInterface.ts", "admin"],
];

const baseArgs = {
    bundle: true,
    write: true,
    sourcemap: !isProdBuild,
    minify: isProdBuild,
    splitting: true,
    treeShaking: true,
    external: ["*.woff", "*.woff2"],
    tsconfig: "./tsconfig.json",
    loader: { ".css": "text", ".md": "text" },
    define: definitions,
    format: "esm",
};

function buildAuthentik(interfaces) {
    const start = Date.now();
    console.clear();
    for (const [source, dest] of interfaces) {
        const DIST = path.join(__dirname, "./dist", dest);
        console.log(`[${new Date(start).toISOString()}] Starting build for target ${source}`);
        try {
            esbuild.buildSync({
                ...baseArgs,
                entryPoints: [`./src/${source}`],
                outdir: DIST,
            });
        } catch (exc) {
            console.error(
                `[${new Date(Date.now()).toISOString()}] Failed to build ${source}: ${exc}`,
            );
            continue;
        }
        const end = Date.now();
        console.log(
            `[${new Date(end).toISOString()}] Finished build for target ${source} in ${Date.now() - start}ms`,
        );
    }
}

let timeoutId = null;
function debouncedBuild() {
    if (timeoutId !== null) {
        clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
        buildAuthentik(interfaces);
    }, 250);
}

if (process.argv.length > 2 && (process.argv[2] === "-h" || process.argv[2] === "--help")) {
    console.log(`Build the authentikUI

options:
  -w, --watch: Build all ${interfaces.length} interfaces
  -p, --proxy: Build only the polyfills and the loading application
  -h, --help: This help message
`);
    process.exit(0);
}

if (process.argv.length > 2 && (process.argv[2] === "-w" || process.argv[2] === "--watch")) {
    console.log("Watching ./src for changes");
    chokidar.watch("./src").on("all", (event, path) => {
        if (!["add", "change", "unlink"].includes(event)) {
            return;
        }
        if (!/(\.css|\.ts|\.js)$/.test(path)) {
            return;
        }
        debouncedBuild();
    });
} else if (process.argv.length > 2 && (process.argv[2] === "-p" || process.argv[2] === "--proxy")) {
    // There's no watch-for-proxy, sorry.
    buildAuthentik(interfaces.slice(0, 2));
    process.exit(0);
} else {
    // And the fallback: just build it.
    buildAuthentik(interfaces);
}
