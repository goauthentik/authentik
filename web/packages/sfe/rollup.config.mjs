/**
 * @file Rollup configuration for the SFE package.
 *
 * @import { RollupOptions } from "rollup";
 */
import { resolvePackage } from "@goauthentik/core/paths/node";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import swc from "@rollup/plugin-swc";
import { resolve as resolvePath } from "node:path";
import copy from "rollup-plugin-copy";

import { DistDirectory } from "../../paths/node.js";

const distDirectory = resolvePath(DistDirectory, "sfe");

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
        copy({
            targets: [
                {
                    src: resolvePackage(
                        "bootstrap",
                        "dist",
                        "css",
                        "bootstrap.min.css",
                        import.meta,
                    ),
                    dest: distDirectory,
                },
            ],
        }),
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

export default config;
