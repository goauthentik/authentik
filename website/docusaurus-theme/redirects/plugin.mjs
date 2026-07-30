/**
 * @file Docusaurus client-side redirects plugin.
 *
 * Exposes parsed redirect entries as Docusaurus global data, allowing the
 * client-side router to follow redirects when it hits a missing page
 * (see `theme/NotFound`).
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 * @import { RedirectEntry } from "./index.mjs"
 */

import { REDIRECTS_PLUGIN_NAME } from "./index.mjs";

/**
 * @typedef {object} AKRedirectsPluginOptions
 * @property {RedirectEntry[]} redirects parsed redirect entries
 */

/**
 * @typedef {AKRedirectsPluginOptions} AKRedirectsPluginData
 */

/**
 * @param {LoadContext} _loadContext
 * @param {AKRedirectsPluginOptions} options
 * @returns {Plugin<AKRedirectsPluginData>}
 */
function akRedirectsPlugin(_loadContext, { redirects }) {
    return {
        name: REDIRECTS_PLUGIN_NAME,

        loadContent() {
            return { redirects };
        },

        contentLoaded({ content, actions }) {
            actions.setGlobalData(content);
        },
    };
}

export default akRedirectsPlugin;
