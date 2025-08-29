/**
 * @file Redirects plugin Node.js utilities.
 *
 * @import { RedirectEntry } from "./index.mjs"
 */

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
