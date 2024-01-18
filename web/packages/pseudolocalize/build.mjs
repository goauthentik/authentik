import * as esbuild from "esbuild";
import { globSync } from "glob";

const tsfiles = globSync("./index.ts");

esbuild
    .build({
        entryPoints: tsfiles,
        outdir: "dist/",
    })
    .catch(() => process.exit(1));
