/**
 * @file Build script for the simplified flow executor (SFE).
 */
import { DistDirectory, PackageRoot } from "@goauthentik/web/paths";
import esbuild from "esbuild";
import copy from "esbuild-plugin-copy";
import { es5Plugin } from "esbuild-plugin-es5";
import { createRequire } from "node:module";
import * as path from "node:path";

const require = createRequire(import.meta.url);

async function buildSFE() {
    const sourceDirectory = path.join(PackageRoot, "packages", "sfe");
    const outDirectory = path.join(DistDirectory, "sfe");

    const bootstrapCSSPath = require.resolve(
        path.join("bootstrap", "dist", "css", "bootstrap.min.css"),
    );

    /**
     * @type {esbuild.BuildOptions}
     */
    const config = {
        tsconfig: path.join(sourceDirectory, "tsconfig.json"),
        entryPoints: [path.join(sourceDirectory, "index.ts")],
        minify: false,
        bundle: true,
        sourcemap: true,

        legalComments: "external",
        platform: "browser",
        format: "iife",
        alias: {
            "@swc/helpers": path.dirname(require.resolve("@swc/helpers/package.json")),
        },
        banner: {
            js: [
                // ---
                "// Simplified Flow Executor (SFE)",
                "// @ts-nocheck",
                "",
            ].join("\n"),
        },
        plugins: [
            copy({
                assets: [
                    {
                        from: bootstrapCSSPath,
                        to: outDirectory,
                    },
                ],
            }),
            es5Plugin({
                swc: {
                    jsc: {
                        loose: false,
                        externalHelpers: false,
                        keepClassNames: false,
                    },
                    minify: false,
                },
            }),
        ],
        target: ["es5"],
        outdir: outDirectory,
    };

    esbuild.build(config);
}

buildSFE()
    .then(() => {
        console.log("Build complete");
    })
    .catch((error) => {
        console.error("Build failed", error);
        process.exit(1);
    });
