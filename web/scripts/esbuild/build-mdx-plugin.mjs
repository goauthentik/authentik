/**
 * @import {
      OnLoadArgs,
      OnLoadResult,
      Plugin,
      PluginBuild
 * } from 'esbuild'
 */
import * as fs from "node:fs/promises";
import * as path from "node:path";

/**
 * @typedef {Omit<OnLoadArgs, 'pluginData'> & LoadDataFields} LoadData
 *   Data passed to `onload`.
 *
 * @typedef LoadDataFields
 *   Extra fields given in `data` to `onload`.
 * @property {PluginData | null | undefined} [pluginData]
 *   Plugin data.
 *
 *
 * @typedef PluginData
 *   Extra data passed.
 * @property {Buffer | string | null | undefined} [contents]
 *   File contents.
 */

const name = "mdx-plugin";

/**
 * @typedef MDXPluginOptions
 *
 * @property {string} root Root directory.
 */

/**
 * Bundle MDX into JSON modules.
 *
 * @param {MDXPluginOptions} options Options.
 * @returns {Plugin} Plugin.
 */
export function mdxPlugin({ root }) {
    /**
     * @param {PluginBuild} build
     */
    function setup(build) {
        /**
         * @param {LoadData} data Data.
         * @returns {Promise<OnLoadResult>} Result.
         */
        async function onload(data) {
            const content = String(
                data.pluginData &&
                    data.pluginData.contents !== null &&
                    data.pluginData.contents !== undefined
                    ? data.pluginData.contents
                    : await fs.readFile(data.path),
            );

            const publicPath = path.resolve(
                "/",
                path.relative(path.join(root, "website"), data.path),
            );
            const publicDirectory = path.dirname(publicPath);

            return {
                contents: JSON.stringify({ content, publicPath, publicDirectory }),
                loader: "file",
            };
        }

        build.onLoad({ filter: /\.mdx?$/ }, onload);
    }

    return { name, setup };
}
