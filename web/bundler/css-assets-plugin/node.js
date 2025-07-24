/**
 * @file CSS asset rewrite plugin for ESBuild.
 *
 * @import { Plugin } from "esbuild"
 */

import * as fs from "node:fs/promises";

/**
 * Rewrite `url()` calls in CSS files to point to the static directory.
 *
 * @returns {Plugin}
 */
export function cssAssetPlugin() {
    return {
        name: "css-text-loader",
        setup: (build) => {
            const URLPattern = /url\(\s*['"]?(?:[./]*)(assets\/[^)'"']*)['"]?\s*\)/g;

            build.onLoad({ filter: /\.css$/ }, async (args) => {
                const contents = await fs.readFile(args.path, "utf8");

                return {
                    loader: "text",
                    contents: contents.replaceAll(URLPattern, "url(./static/dist/$1)"),
                };
            });
        },
    };
}
