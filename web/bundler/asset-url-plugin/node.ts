/**
 * @file Emits `?url` and `?worker&url` imports as files, mirroring Vite's import suffixes.
 */

import { readFile } from "node:fs/promises";
import { basename, dirname, extname, join } from "node:path";

import type { BuildOptions, Plugin } from "esbuild";

const Namespace = "asset-url";

/**
 * Matches `?url` and `?worker&url` at the end of an import path.
 */
const AssetURLPattern = /\?(worker&)?url$/;

/**
 * Options the worker bundles share with the main build.
 */
export type WorkerBuildOptions = Pick<
    BuildOptions,
    "alias" | "conditions" | "define" | "minify" | "tsconfig"
>;

/**
 * Import a file's URL relative to the importing module, for use with `new URL(url,
 * import.meta.url)`.
 *
 * - `?url` copies the file as is.
 * - `?worker&url` first bundles the file into a self-contained module worker.
 */
export function assetURLPlugin(workerOptions: WorkerBuildOptions = {}): Plugin {
    return {
        name: "asset-url",
        setup(build) {
            build.onResolve({ filter: AssetURLPattern }, async (args) => {
                const worker = args.path.endsWith("?worker&url");
                const specifier = args.path.replace(AssetURLPattern, "");

                const resolved = await build.resolve(specifier, {
                    kind: args.kind,
                    resolveDir: args.resolveDir,
                    importer: args.importer,
                });

                if (resolved.errors.length) {
                    return { errors: resolved.errors };
                }

                // The emitted file keeps this path's name and extension.
                const path = worker
                    ? join(
                          dirname(resolved.path),
                          `${basename(resolved.path, extname(resolved.path))}.js`,
                      )
                    : resolved.path;

                return {
                    path,
                    namespace: Namespace,
                    pluginData: { source: resolved.path, worker },
                };
            });

            build.onLoad({ filter: /.*/, namespace: Namespace }, async (args) => {
                const { source, worker } = args.pluginData as { source: string; worker: boolean };

                if (!worker) {
                    return {
                        contents: await readFile(source),
                        loader: "file",
                        watchFiles: [source],
                    };
                }

                const result = await build.esbuild.build({
                    ...workerOptions,
                    entryPoints: [source],
                    bundle: true,
                    write: false,
                    format: "esm",
                    platform: "browser",
                    metafile: true,
                    logLevel: "silent",
                });

                return {
                    contents: result.outputFiles[0].contents,
                    loader: "file",
                    warnings: result.warnings,
                    watchFiles: Object.keys(result.metafile.inputs).map((input) =>
                        join(process.cwd(), input),
                    ),
                };
            });
        },
    };
}
