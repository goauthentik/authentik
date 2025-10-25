/* eslint-disable no-console */
/**
 * @file Docusaurus releases plugin.
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 * @import { AKReleasesPluginEnvironment } from "./node.mjs"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { collectReleaseFiles, prepareReleaseEnvironment } from "./node.mjs";

const PLUGIN_NAME = "ak-releases-plugin";
const RELEASES_FILENAME = "releases.gen.json";

/**
 * @typedef {object} AKReleasesPluginOptions
 * @property {string} docsDirectory The path to the documentation directory.
 * @property {AKReleasesPluginEnvironment} [environment] Optional environment variables overrides.
 */

/**
 * @typedef {object} AKReleasesPluginData
 * @property {string} publicPath URL to the plugin's public directory.
 * @property {string[]} releases Available versions of the documentation.
 * @property {AKReleasesPluginEnvironment} env Environment variables
 */

/**
 * @param {LoadContext} loadContext
 * @param {AKReleasesPluginOptions} options
 * @returns {Promise<Plugin<AKReleasesPluginData>>}
 */
async function akReleasesPlugin(loadContext, options) {
    return {
        name: PLUGIN_NAME,

        async loadContent() {
            console.log(`🚀 ${PLUGIN_NAME} loaded`);

            const environment = {
                ...prepareReleaseEnvironment(),
                ...options.environment,
            };

            const releases = collectReleaseFiles(options.docsDirectory).map(
                (release) => release.name,
            );

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
                env: environment,
            };

            content.publicPath;

            return content;
        },

        contentLoaded({ content, actions }) {
            const { setGlobalData } = actions;

            setGlobalData(content);
        },
    };
}

export default akReleasesPlugin;
