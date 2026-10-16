/**
 * @import { LoadContext, Plugin } from "@docusaurus/types";
 * @import { SearchGlobalData } from "./common.mjs";
 * @import { BuildReport } from "./node.mjs";
 * @file The Docusaurus plugin that builds the search index.
 *   The index and the sqlite-wasm runtime are written into the site's `static/search/` directory
 *   while content loads, so `docusaurus build` publishes them and `docusaurus start` serves them.
 *   After a production build, every URL the index holds for this site is checked against the
 *   routes Docusaurus built.
 */

import { resolve } from "node:path";

import { trimTrailingSlashes } from "../llms-txt/common.mjs";
import {
    PLUGIN_NAME,
    SEARCH_DIRECTORY,
    SEARCH_INDEX_FILENAME,
    SEARCH_WORKER_FILENAME,
    sqliteRuntimeDirectory,
} from "./common.mjs";
import { buildSearchIndex, describeBuild, sqliteRuntimeVersion } from "./node.mjs";
import { assertSearchSite, loadSearchSites } from "./sites.mjs";

/**
 * @typedef {object} AKSearchPluginOptions
 * @property {string} site The id of the site being built, as listed in `sites.mjs`.
 * @property {string} [endpoint] The URL of the hosted search endpoint, the worker under
 *   `website/search-worker`. Set, the browser queries it and opens its own copy of the index
 *   only when a request fails. Unset, the browser opens its own copy for every search.
 */

/**
 * The dev server reloads content on every source change. The index is built once per process
 * there, and on every load of a production build.
 */
let builtInDevServer = false;

/**
 * @param {LoadContext} context
 * @param {AKSearchPluginOptions} options
 *
 * @returns {Plugin<BuildReport | null>}
 */
export default function akSearchPlugin(context, options) {
    assertSearchSite(options.site);

    const websiteDir = resolve(context.siteDir, "..");
    const sites = loadSearchSites(websiteDir);
    const site = /** @type {import("./common.mjs").SearchSite} */ (
        sites.find((candidate) => candidate.id === options.site)
    );
    const outputDir = resolve(context.siteDir, "static", SEARCH_DIRECTORY);
    const production = process.env.NODE_ENV === "production";

    return {
        name: PLUGIN_NAME,

        loadContent() {
            if (!production && builtInDevServer) return null;

            const report = buildSearchIndex({
                websiteDir,
                sites,
                currentSite: site.id,
                outputDir,
                onFallback(filePath, error) {
                    console.warn(
                        `${PLUGIN_NAME}: read ${filePath} as plain Markdown: ${error instanceof Error ? error.message : String(error)}`,
                    );
                },
            });

            builtInDevServer = true;
            console.log(`${PLUGIN_NAME}: ${describeBuild(report)}`);

            return report;
        },

        contentLoaded({ actions }) {
            const base = `${context.baseUrl}${SEARCH_DIRECTORY}/`;

            /** @type {SearchGlobalData} */
            const data = {
                site: site.label,
                endpoint: options.endpoint ?? null,
                indexPath: `${base}${SEARCH_INDEX_FILENAME}`,
                workerPath: `${base}${SEARCH_WORKER_FILENAME}`,
                runtimePath: `${base}${sqliteRuntimeDirectory(sqliteRuntimeVersion())}/`,
            };

            actions.setGlobalData(data);
        },

        postBuild({ content, routesPaths }) {
            if (!content) return;

            const routes = new Set(routesPaths.map((route) => trimTrailingSlashes(route) || "/"));
            const missing = content.currentURLs.filter(
                (url) => !routes.has(trimTrailingSlashes(url) || "/"),
            );

            if (missing.length) {
                throw new Error(
                    `${PLUGIN_NAME}: ${missing.length} indexed URL(s) of this site match no built route:\n${missing
                        .slice(0, 20)
                        .map((url) => `  ${url}`)
                        .join("\n")}`,
                );
            }
        },
    };
}
