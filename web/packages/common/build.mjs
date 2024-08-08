import * as esbuild from "esbuild";
import fs from "fs";
import { globSync } from "glob";
import path from "path";
import { cwd } from "process";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const isProdBuild = process.env.NODE_ENV === "production";

const apiBasePath = process.env.AK_API_BASE_PATH || "";

const definitions = {
    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
    "process.env.CWD": JSON.stringify(cwd()),
    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
};

const otherFiles = [["src/styles/**", "styles"]];

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

const tsfiles = globSync("src/**/*.ts");

esbuild
    .build({
        entryPoints: tsfiles,
        sourcemap: true,
        bundle: false,
        tsconfig: "./tsconfig.build.json",
        outdir: "dist/",
        format: "esm",
        define: definitions,
        loader: { ".css": "text" },
    })
    .catch(() => process.exit(1));
