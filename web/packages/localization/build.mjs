import * as esbuild from "esbuild";

esbuild
    .build({
        entryPoints: ["src/locale-codes.ts"],
        outdir: "dist",
    })
    .catch(() => process.exit(1));

esbuild
    .build({
        entryPoints: ["src/locales/*.ts"],
        outdir: "dist/locales",
    })
    .catch(() => process.exit(1));
