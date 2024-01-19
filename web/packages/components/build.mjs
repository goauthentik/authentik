import * as esbuild from "esbuild";
import { globSync } from "glob";

const tsfiles = globSync('src/**/*.ts');

esbuild
    .build({
        entryPoints: tsfiles,
        outdir: "dist/",
        loader: { '.css': 'text' },
    })
    .catch(() => process.exit(1));
