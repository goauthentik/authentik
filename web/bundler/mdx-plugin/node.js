/**
 * @file MDX plugin for ESBuild.
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

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

/**
 * @typedef {Omit<OnLoadArgs, 'pluginData'> & LoadDataFields} LoadData Data passed to `onload`.
 *
 * @typedef LoadDataFields Extra fields given in `data` to `onload`.
 * @property {PluginData | null | undefined} [pluginData] Plugin data.
 *
 * @typedef PluginData Extra data passed.
 * @property {Buffer | string | null | undefined} [contents] File contents.
 */

const pluginName = "mdx-plugin";

/**
 * @typedef MDXPluginOptions
 *
 * @property {string} root Root directory.
 */

/**
 * Bundle MDX into JSON modules.
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
         * @param {LoadData} data
         * @returns {Promise<OnLoadResult>}
         */
        async function loadListener(data) {
            const content = String(
                data.pluginData &&
                    data.pluginData.contents !== null &&
                    data.pluginData.contents !== undefined
                    ? data.pluginData.contents
                    : await fs.readFile(data.path),
            );

            const publicPath = path.resolve(
                "/",
                path.relative(path.join(root, "website", "docs"), data.path),
            );
            const publicDirectory = path.dirname(publicPath);

            return {
                contents: JSON.stringify({ content, publicPath, publicDirectory }),
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
