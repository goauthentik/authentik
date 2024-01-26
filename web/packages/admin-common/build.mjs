import * as esbuild from "esbuild";
import { globSync } from "glob";

const tsfiles = globSync("src/**/*.ts");

esbuild
    .build({
        entryPoints: tsfiles,
        outdir: "dist/",
        tsconfig: "./tsconfig.build.json",
        loader: { ".css": "text" },
    })
    .catch(
        // eslint-disable-next-line no-undef
        () => process.exit(1),
    );
