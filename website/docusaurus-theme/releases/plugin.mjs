/* eslint-disable no-console */
/**
 * @file Docusaurus releases plugin.
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { collectReleaseFiles } from "./utils.mjs";

const PLUGIN_NAME = "ak-releases-plugin";
const RELEASES_FILENAME = "releases.gen.json";

/**
 * @typedef {object} ReleasesPluginOptions
 * @property {string} docsDirectory The path to the documentation directory.
 */

/**
 * @typedef {object} AKReleasesPluginData
 * @property {string} publicPath The URL to the plugin's public directory.
 * @property {string[]} releases The available versions of the documentation.
 */

/**
 * @param {LoadContext} loadContext
 * @param {ReleasesPluginOptions} options
 * @returns {Promise<Plugin<AKReleasesPluginData>>}
 */
async function akReleasesPlugin(loadContext, { docsDirectory }) {
    return {
        name: PLUGIN_NAME,

        async loadContent() {
            console.log(`🚀 ${PLUGIN_NAME} loaded`);

            const releases = collectReleaseFiles(docsDirectory).map((release) => release.name);

            const outputPath = path.join(loadContext.siteDir, "static", RELEASES_FILENAME);

            await fs.mkdir(path.dirname(outputPath), { recursive: true });
            await fs.writeFile(outputPath, JSON.stringify(releases, null, 2), "utf-8");
            console.log(`✅ ${RELEASES_FILENAME} generated`);

            /**
             * @type {AKReleasesPluginData}
             */
            const content = {
                releases,
                publicPath: path.join("/", RELEASES_FILENAME),
            };

            return content;
        },

        contentLoaded({ content, actions }) {
            const { setGlobalData } = actions;

            setGlobalData(content);
        },
    };
}

export default akReleasesPlugin;
