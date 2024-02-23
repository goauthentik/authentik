import esbuild from "esbuild";
import fs from "fs";
import { globSync } from "glob";
import path from "path";
import { cwd } from "process";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
export const ROOT = path.join(__dirname, ".");
export const DIST = path.join(ROOT, "../../dist/admin");

const definitions = {
    "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
    "process.env.CWD": JSON.stringify(cwd()),
    "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
};

const tsfiles = globSync(path.join(ROOT, "./src/**/*.ts"));
const otherFiles = [
    ["node_modules/@patternfly/patternfly/patternfly.min.css", "."],
    ["src/common/styles/*", "."],
    ["src/custom.css", "."],
    ["node_modules/@patternfly/patternfly/assets/*", "./assets"],
    ["src/assets/images/*", "./assets/images"],
    ["./icons/*", "./assets/icons"],
];

for (const obj of ["obj", "dist"]) {
    for (const [source, dest] of otherFiles) {
        const target = path.join(__dirname, obj, dest);
        fs.mkdirSync(target, { recursive: true });
        fs.copyfileSync(source, target);
    }
}

esbuild.buildSync({
    entryPoints: tsfiles,
    outdir: "obj/",
    tsconfig: "./tsconfig.json",
    loader: { ".css": "text", ".md": "text" },
});
