import esbuild from "esbuild";
import { globSync } from "glob";
import path from "path";
import { cwd } from "process";
import { fileURLToPath } from "url";

import { apiBasePath, isProdBuild } from "../../rollup.base.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
export const ROOT = path.join(__dirname, ".");
export const DIST = path.join(ROOT, "../../dist/admin");

const definitions = {
    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
    "process.env.CWD": JSON.stringify(cwd()),
    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
};

const tsfiles = globSync("src/**/*.ts");

/*
  esbuild.buildSync({
    entryPoints: tsfiles,
    outdir: "dist/",
    tsconfig: "./tsconfig.build.json",
    loader: { ".css": "text", ".md": "text" },
});
*/

esbuild.buildSync({
    entryPoints: ["./dist/AdminInterface.js"],
    outdir: DIST,
    bundle: true,
    write: true,
    splitting: true,
    external: ["*.woff", "*.woff2"],
    tsconfig: "./tsconfig.build.json",
    loader: { ".css": "text", ".md": "text" },
    define: definitions,
    format: "esm",
});
