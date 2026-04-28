/* eslint-disable no-console */
/**
 * @file Docusaurus client-side redirects plugin.
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 * @import { RedirectEntry } from "./index.mjs"
 */

const PLUGIN_NAME = "ak-redirects-plugin";

/**
 * @typedef {object} AKRedirectsPluginOptions
 * @property {RedirectEntry[]} redirects parsed redirect entries
 */

/**
 * @typedef {object} AKRedirectsPluginData
 * @property {RedirectEntry[]} redirects parsed redirect entries
 */

/**
 * @param {LoadContext} _loadContext
 * @param {AKRedirectsPluginOptions} options
 * @returns {Promise<Plugin<AKRedirectsPluginData>>}
 */
async function akRedirectsPlugin(_loadContext, { redirects }) {
    return {
        name: PLUGIN_NAME,

        async loadContent() {
            console.log(`🚀 ${PLUGIN_NAME} loaded`);

            /**
             * @type {AKRedirectsPluginData}
             */
            const content = { redirects };

            return content;
        },

        contentLoaded({ content, actions }) {
            const { setGlobalData } = actions;

            setGlobalData(content);
        },
    };
}

export default akRedirectsPlugin;
