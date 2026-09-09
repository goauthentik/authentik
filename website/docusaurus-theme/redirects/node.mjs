/**
 * @file Redirects plugin Node.js utilities.
 *
 * @import { PluginConfig } from "@docusaurus/types"
 * @import { Options as ClientRedirectsOptions } from "@docusaurus/plugin-client-redirects"
 * @import { RedirectEntry } from "./index.mjs"
 */

import { RewriteIndex } from "./index.mjs";

import { parseAllRedirects } from "netlify-redirect-parser";

/**
 * @param {string[]} redirectsFiles
 * @returns {Promise<RedirectEntry[]>}
 */
export async function parse(...redirectsFiles) {
    const redirectsFileContent = await parseAllRedirects({
        redirectsFiles,
        configRedirects: [],
        minimal: true,
    });

    if (redirectsFileContent.errors.length) {
        console.error(redirectsFileContent.errors);
        throw new TypeError("Failed to parse redirects file.");
    }

    /**
     * @type {RedirectEntry[]}
     */
    // @ts-expect-error - dynamically generated.
    const redirectEntries = redirectsFileContent.redirects;

    return redirectEntries;
}

/**
 * Create the pair of plugins wiring a Netlify `_redirects` file into a site:
 *
 * 1. `redirects/plugin` exposes the parsed entries as global data, so the
 *    client-side router can follow redirects when navigating to a missing
 *    page (see `theme/NotFound`).
 * 2. `@docusaurus/plugin-client-redirects` creates build-time redirect pages
 *    for HTTP navigation. Netlify's deployment additionally picks up the
 *    `_redirects` file itself, covering sources no longer present in the
 *    build output, such as removed, renamed, or moved pages.
 *
 * @param {string} redirectsFile absolute path to a Netlify `_redirects` file
 * @param {Omit<ClientRedirectsOptions, "createRedirects">} [clientRedirectsOptions]
 *   extra options for `@docusaurus/plugin-client-redirects`, e.g. static `redirects`
 * @returns {Promise<PluginConfig[]>}
 */
export async function createRedirectPlugins(redirectsFile, clientRedirectsOptions = {}) {
    const redirects = await parse(redirectsFile);
    const rewriteIndex = new RewriteIndex(redirects);

    return [
        ["@goauthentik/docusaurus-theme/redirects/plugin", { redirects }],
        [
            "@docusaurus/plugin-client-redirects",
            /** @type {ClientRedirectsOptions} */ ({
                ...clientRedirectsOptions,
                createRedirects: (existingPath) => rewriteIndex.findAliases(existingPath),
            }),
        ],
    ];
}
