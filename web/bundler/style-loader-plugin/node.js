/**
 * @file MDX plugin for ESBuild.
 *
 * @import { Plugin, PluginBuild } from "esbuild"
 */

import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

import { resolvePackage } from "@goauthentik/core/paths/node";

const CSSNamespace = /** @type {const} */ ({
    Global: "css-global",
    Process: "css-process",
    Bundled: "css-bundled",
});

/**
 * Selectively apply the ESBuild `css` loader.
 *
 * @returns {Plugin}
 */
export function styleLoaderPlugin() {
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

                // Resolve the CSS content by bundling it with ESBuild.
                const result = await build.esbuild.build({
                    stdin: {
                        contents: cssContent,
                        resolveDir: dirname(args.path),
                        loader: "css",
                    },
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
                });

                const bundledCSS = result.outputFiles[0].text;

                return {
                    contents: bundledCSS,
                    loader: "text",
                };
            });
        },
    };
}
