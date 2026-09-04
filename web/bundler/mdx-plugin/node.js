/**
 * @file Markdown plugin for ESBuild.
 *
 * Resolves `~docs/...` imports to the website docs tree, then compiles each
 * `.md` / `.mdx` file to HTML at build time. The compiled HTML uses
 * `<ak-md-a>` and `<ak-alert>` custom elements so the runtime side can
 * stamp the HTML directly into shadow DOM without any client-side
 * JavaScript evaluation — this is what lets the page CSP drop
 * `'unsafe-eval'`.
 *
 * The on-load result is shipped via the `file` loader so the JSON travels
 * over the existing fetch-then-set-innerHTML path used by `<ak-mdx>`. The
 * shape is `{ content, frontmatter, publicPath, publicDirectory }` where
 * `content` is now pre-rendered HTML rather than raw markdown source.
 *
 * @import {
 *   OnLoadArgs,
 *   OnLoadResult,
 *   OnResolveArgs,
 *   OnResolveResult,
 *   Plugin,
 *   PluginBuild
 * } from "esbuild"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { compileMarkdown } from "./compile.js";

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

const pluginName = "mdx-plugin";

/**
 * @typedef MDXPluginOptions
 * @property {string} root Repository root.
 */

/**
 * Bundle markdown and MDX source into JSON modules.
 *
 * @param {MDXPluginOptions} options
 * @returns {Plugin}
 */
export function mdxPlugin({ root }) {
    const prefix = "~docs";
    // TODO: Replace with `resolvePackage` after NPM Workspaces support is added.
    const docsPackageRoot = path.resolve(MonoRepoRoot, "website");

    /**
     * @param {PluginBuild} build
     */
    function setup(build) {
        /**
         * @param {OnResolveArgs} args
         * @returns {Promise<OnResolveResult>}
         */
        async function resolveListener(args) {
            if (!args.path.startsWith("~")) return args;

            return {
                path: path.join(docsPackageRoot, "docs", args.path.slice(prefix.length)),
                pluginName,
            };
        }

        /**
         * @param {OnLoadArgs} args
         * @returns {Promise<OnLoadResult>}
         */
        async function loadListener(args) {
            const source = String(await fs.readFile(args.path));

            const publicPath = path.resolve(
                "/",
                path.relative(path.join(root, "website", "docs"), args.path),
            );
            const publicDirectory = path.dirname(publicPath);

            const { html, frontmatter } = await compileMarkdown(source, publicDirectory);

            return {
                contents: JSON.stringify({
                    content: html,
                    frontmatter,
                    publicPath,
                    publicDirectory,
                }),
                loader: "file",
                pluginName,
            };
        }

        build.onResolve({ filter: /\.mdx?$/ }, resolveListener);
        build.onLoad({ filter: /\.mdx?$/ }, loadListener);
    }

    return {
        name: pluginName,
        setup,
    };
}
