/**
 * @file The sites one index covers. Every site build indexes all of them, so a reader on any
 *   site can find a page on any other.
 */

import { createRequire } from "node:module";
import { resolve } from "node:path";

import { DocusaurusURLByEnvironment } from "@goauthentik/docusaurus-config";

/**
 * A hit on another site links to the published site whatever the environment, so a reader of a
 * dev server or a deploy preview lands on a page that exists.
 */
const PublishedURL = DocusaurusURLByEnvironment.production;

/**
 * @import { SearchSite } from "./common.mjs";
 */

const require = createRequire(import.meta.url);

/**
 * @typedef {Omit<SearchSite, "categories"> & { categoriesFile?: string }} SearchSiteSource
 *
 *   A site whose category labels live in a module of its own directory, read when the sites are
 *   loaded. A theme module cannot import a sibling site's file directly: the theme is its own
 *   TypeScript project, and a file outside it is not part of the build.
 */

/**
 * @type {readonly SearchSiteSource[]}
 */
const SITE_SOURCES = [
    {
        id: "docs",
        label: "Documentation",
        directory: "docs",
        url: PublishedURL.Docs,
        routeBasePath: "/",
        categoriesFile: "topics.mjs",
        ignoreFiles: ["developer-docs/api/reference/**"],
    },
    {
        id: "integrations",
        label: "Integrations",
        directory: "integrations",
        url: PublishedURL.Integrations,
        routeBasePath: "/",
        categoriesFile: "categories.mjs",
        ignoreFiles: ["template/**"],
    },
    {
        id: "api",
        label: "API",
        directory: "api",
        // The API site is generated from the schema, and its reference pages exist only after
        // `docusaurus gen-api-docs` has run. The hand-written pages are indexed on every build.
        url: process.env.API_REFERENCE_ORIGIN || "https://api.goauthentik.io",
        routeBasePath: "/",
        category: "API",
    },
];

/**
 * The ids a plugin or the CLI may name.
 */
export const SearchSiteIDs = SITE_SOURCES.map((site) => site.id);

/**
 * Load the sites with their category labels.
 *
 * @param {string} websiteDir The absolute path of `website/`.
 *
 * @returns {SearchSite[]}
 */
export function loadSearchSites(websiteDir) {
    return SITE_SOURCES.map(({ categoriesFile, ...site }) => {
        if (!categoriesFile) return site;

        const loaded = /** @type {{ default: readonly (readonly [string, string])[] }} */ (
            require(resolve(websiteDir, site.directory, categoriesFile))
        );

        return { ...site, categories: loaded.default };
    });
}

/**
 * @param {string} id
 */
export function assertSearchSite(id) {
    if (!SearchSiteIDs.includes(id)) {
        throw new Error(
            `search: unknown site "${id}"; expected one of ${SearchSiteIDs.join(", ")}`,
        );
    }
}
