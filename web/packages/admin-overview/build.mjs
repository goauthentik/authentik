import esbuild from "esbuild";
import { globSync } from "glob";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
export const ROOT = path.join(__dirname, ".");
export const DIST = path.join(ROOT, "../../dist/admin");

const tsfiles = globSync("src/**/*.ts");

esbuild.buildSync({
    entryPoints: tsfiles,
    outdir: "dist/",
    tsconfig: "./tsconfig.build.json",
    loader: { ".css": "text" },
});
