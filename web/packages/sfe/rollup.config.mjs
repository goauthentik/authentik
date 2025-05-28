/**
 * @file Rollup configuration for the SFE package.
 */
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import swc from "@rollup/plugin-swc";
import { resolve as resolvePath } from "node:path";
import copy from "rollup-plugin-copy";

export async function createConfig() {
    // TODO: Move this to a synchronous import once the repo root has NPM Workspaces.
    const { resolvePackage, MonoRepoRoot } = await import("@goauthentik/core/paths/node");

    const distDirectory = resolvePath(MonoRepoRoot, "web", "dist", "sfe");
    const bootstrapDirectory = resolvePackage("bootstrap", import.meta);

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
                        src: resolvePath(bootstrapDirectory, "dist", "css", "bootstrap.min.css"),
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

    return config;
}

console.log("Preparing SFE package...");

export default createConfig;
