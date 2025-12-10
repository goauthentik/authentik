/**
 * @file Rollup configuration for the SFE package.
 * @import { Plugin, RollupOptions } from "rollup";
 */

import * as fs from "node:fs/promises";
import { join } from "node:path";

import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import swc from "@rollup/plugin-swc";

export async function createConfig() {
    // Rollup's CJS to ESM conversion doesn't work well with sub-dependencies.
    // We use an async import to fix the issue.
    const { resolvePackage, MonoRepoRoot } = await import("@goauthentik/core/paths/node");

    const distDirectory = join(MonoRepoRoot, "web", "dist", "sfe");
    const bootstrapDirectory = resolvePackage("bootstrap", import.meta);

    /**
     * @type {Plugin} A plugin to copy static assets.
     */
    const copyPlugin = {
        name: "copy-static-assets",
        buildEnd: async () => {
            console.log("Copying static assets...");

            const bootstrapCSSFilePath = join(
                bootstrapDirectory,
                "dist",
                "css",
                "bootstrap.min.css",
            );

            await fs.mkdir(distDirectory, { recursive: true });
            await fs.copyFile(bootstrapCSSFilePath, join(distDirectory, "bootstrap.min.css"));
        },
    };

    /**
     * @type {RollupOptions}
     */
    const config = {
        input: "src/index.ts",
        output: {
            dir: distDirectory,
            format: "cjs",
        },
        context: "window",
        plugins: [
            copyPlugin,
            resolve({ browser: true }),
            commonjs(),
            swc({
                swc: {
                    jsc: {
                        loose: false,
                        externalHelpers: false,
                        // Requires v1.2.50 or upper and requires target to be es2016 or upper.
                        keepClassNames: false,
                    },
                    minify: false,
                    env: {
                        targets: {
                            edge: "17",
                            ie: "11",
                        },
                        mode: "entry",
                    },
                },
            }),
        ],
    };

    return config;
}

console.log("Preparing SFE package...");

export default createConfig;
