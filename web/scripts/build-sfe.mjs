/**
 * @file Build script for the simplified flow executor (SFE).
 */
import { DistDirectory, PackageRoot } from "@goauthentik/web/paths";
import esbuild from "esbuild";
import copy from "esbuild-plugin-copy";
import { es5Plugin } from "esbuild-plugin-es5";
import { createRequire } from "node:module";
import * as path from "node:path";

/**
 * Builds the Simplified Flow Executor bundle.
 *
 * @remarks
 * The output directory and file names are referenced by the backend.
 * @see {@link ../../authentik/flows/templates/if/flow-sfe.html}
 * @returns {Promise<void>}
 */
async function buildSFE() {
    const require = createRequire(import.meta.url);

    const sourceDirectory = path.join(PackageRoot, "sfe");

    const entryPoint = path.join(sourceDirectory, "main.js");
    const outDirectory = path.join(DistDirectory, "sfe");

    const bootstrapCSSPath = require.resolve(
        path.join("bootstrap", "dist", "css", "bootstrap.min.css"),
    );

    /**
     * @type {esbuild.BuildOptions}
     */
    const config = {
        tsconfig: path.join(sourceDirectory, "tsconfig.json"),
        entryPoints: [entryPoint],
        minify: false,
        bundle: true,
        sourcemap: true,
        treeShaking: true,
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
                `// Bundled on ${new Date().toISOString()}`,
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
