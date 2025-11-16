/**
 * @file MDX plugin for ESBuild.
 *
 * @import { Plugin, PluginBuild, BuildContext, BuildOptions } from "esbuild"
 * @import { BaseLogger } from "pino"
 */

import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, relative } from "node:path";

import { ConsoleLogger } from "#logger/node";

import { resolvePackage } from "@goauthentik/core/paths/node";

const CSSNamespace = /** @type {const} */ ({
    Global: "css-global",
    Process: "css-process",
    Bundled: "css-bundled",
});

/**
 * @typedef StyleLoaderPluginOptions
 *
 * @property {boolean} [watch] Whether to watch for file changes.
 * @property {BaseLogger} [logger]
 */

/**
 * Selectively apply the ESBuild `css` loader.
 *
 * @param {StyleLoaderPluginOptions} [options]
 * @returns {Plugin}
 */
export function styleLoaderPlugin({
    watch = false,
    logger = ConsoleLogger.child({ name: "style-loader-plugin" }),
} = {}) {
    const patternflyPath = resolvePackage("@patternfly/patternfly", import.meta);
    const require = createRequire(import.meta.url);

    /**
     * Apply custom resolution for Patternfly font files.
     *
     * This is necessary because Patternfly's CSS references fonts via relative paths
     * that ESBuild cannot resolve automatically.
     * @type {Parameters<PluginBuild["onResolve"]>}
     */
    const fontResolverArgs = [
        { filter: /\.woff2?$/ },
        async (args) => {
            if (!args.resolveDir.startsWith(patternflyPath)) {
                return;
            }

            return {
                path: join(patternflyPath, args.path),
            };
        },
    ];

    return {
        name: "global-css-plugin",
        setup(build) {
            const { absWorkingDir = process.cwd() } = build.initialOptions;

            /**
             * @type {Map<string, BuildContext>}
             */
            const disposables = new Map();

            build.onDispose(async () => {
                for (const [filePath, ctx] of disposables) {
                    logger.debug(`Disposing CSS build context for ${filePath}`);
                    await ctx.dispose();
                }
            });

            build.onLoad({ filter: /patternfly-base.css/ }, () => {
                return {
                    contents: "",
                    loader: "text",
                };
            });

            build.onResolve(...fontResolverArgs);

            /**
             * Files which should be processed as CSS throughout ESBuild's loader chain.
             */
            build.onResolve({ filter: /\.css$/ }, (args) => {
                if (args.path.endsWith(".global.css") || args.namespace === CSSNamespace.Process) {
                    return {
                        path: require.resolve(args.path, { paths: [args.resolveDir] }),
                        namespace: CSSNamespace.Process,
                    };
                }

                /**
                 * Files imported via `with { type: "bundled-text" }`
                 */
                if (args.with.type === "bundled-text") {
                    return {
                        path: require.resolve(args.path, { paths: [args.resolveDir] }),
                        namespace: CSSNamespace.Bundled,
                    };
                }
            });

            /**
             * Handle `.global.css` files
             *
             * Load as normal CSS...
             */
            build.onLoad({ filter: /.*/, namespace: CSSNamespace.Process }, async (args) => {
                return {
                    contents: await readFile(args.path, "utf8"),
                    loader: "css",
                    resolveDir: dirname(args.path),
                };
            });

            /**
             * Handle `with { type: "bundled-text" }` imports.
             *
             * Bundle the CSS and return as text...
             */
            build.onLoad({ filter: /.*/, namespace: CSSNamespace.Bundled }, async (args) => {
                const cssContent = await readFile(args.path, "utf8");
                let context = disposables.get(args.path);

                /**
                 * @type {BuildOptions}
                 */
                const buildOptions = {
                    stdin: {
                        contents: cssContent,
                        resolveDir: dirname(args.path),
                        loader: "css",
                    },
                    metafile: true,
                    bundle: true,
                    write: false,
                    minify: build.initialOptions.minify || false,
                    logLevel: "silent",
                    loader: { ".woff": "empty", ".woff2": "empty" },
                    plugins: [
                        {
                            name: "font-resolver",
                            setup(fontBuild) {
                                fontBuild.onResolve(...fontResolverArgs);
                            },
                        },
                    ],
                };

                if (!watch) {
                    const result = await build.esbuild.build(buildOptions);
                    const bundledCSS = result.outputFiles?.[0].text;

                    return {
                        contents: bundledCSS,
                        loader: "text",
                    };
                }

                if (!context) {
                    const relativePath = relative(absWorkingDir, args.path);
                    logger.debug(`Watching ${relativePath}`);
                    context = await build.esbuild.context(buildOptions);

                    disposables.set(args.path, context);
                } else {
                    await context.cancel();
                }

                // Resolve the CSS content by bundling it with ESBuild.
                const result = await context.rebuild();

                const bundledCSS = result.outputFiles?.[0].text;
                const { inputs = {} } = result.metafile || {};
                const relativePaths = Object.keys(inputs).filter((path) => path !== "<stdin>");
                const watchFiles = relativePaths.map((path) => join(absWorkingDir, path));

                return {
                    contents: bundledCSS,
                    loader: "text",
                    watchFiles,
                };
            });
        },
    };
}
