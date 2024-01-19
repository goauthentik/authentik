import * as esbuild from "esbuild";
import path from "path";
import { cwd } from "process";
import { fileURLToPath } from "url";

import { apiBasePath, isProdBuild } from "../../rollup.base.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
export const ROOT = path.join(__dirname, ".");
export const DIST = path.join(ROOT, "../../dist/standalone/api-browser");

const definitions = {
    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
    "process.env.CWD": JSON.stringify(cwd()),
    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
};

esbuild
    .build({
        entryPoints: ["./src/index.ts"],
        outdir: DIST,
        bundle: true,
        write: true,
        external: ["*.woff", "*.woff2"],
        define: definitions,
    })
    .catch(() => process.exit(1));
