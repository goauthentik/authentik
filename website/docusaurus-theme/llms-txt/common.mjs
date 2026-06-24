/**
 * @file Types and option normalization for the llms.txt plugin.
 */

/**
 * @typedef {object} AKLlmsDocsSection
 * @property {string} path Filesystem path relative to siteDir (e.g. ".", "docs").
 * @property {string} routeBasePath Docusaurus routeBasePath for the section (e.g. "/").
 * @property {string} [label] Optional heading shown when grouping is flat.
 */

/**
 * @typedef {object} AKLlmsCrossLink
 * @property {string} label
 * @property {string} url
 */

/**
 * @typedef {object} AKLlmsPluginOptions
 * @property {string} [siteUrl] Overrides the site URL from Docusaurus config.
 * @property {string} [title] Overrides the site title.
 * @property {string} [description] Overrides the site tagline.
 * @property {AKLlmsDocsSection[]} sections One or more docs roots to scan.
 * @property {string[]} [ignoreFiles] Extra glob patterns to exclude.
 * @property {AKLlmsCrossLink[]} [crossLinks] Sibling-site links for the header.
 * @property {"topic"|"category"} [groupBy] How to group the root index.
 * @property {[string, string][]} [categories] [dirName, label] pairs (integrations).
 */

/**
 * @typedef {object} AKLlmsDocInfo
 * @property {string} title
 * @property {string} path Site-relative source path, POSIX separators, no extension.
 * @property {string} url Absolute URL of the rendered page.
 * @property {string} description
 * @property {string} content Cleaned Markdown body.
 * @property {string} [group] Topic dir or category label for grouping.
 */

export const LLMS_TXT_FILENAME = "llms.txt";
export const LLMS_FULL_FILENAME = "llms-full.txt";

/**
 * Validate and apply defaults to plugin options.
 *
 * @param {Partial<AKLlmsPluginOptions>} options
 * @returns {Required<Pick<AKLlmsPluginOptions, "sections" | "ignoreFiles" | "crossLinks" | "groupBy">> & AKLlmsPluginOptions}
 */
export function normalizeOptions(options) {
    if (!options || !Array.isArray(options.sections) || options.sections.length === 0) {
        throw new Error("llms.txt plugin requires a non-empty `sections` array.");
    }

    return {
        ...options,
        // Re-assert the guard-narrowed `sections` so the return type satisfies
        // Required<Pick<…, "sections">> (the Partial spread widens it to optional).
        sections: options.sections,
        ignoreFiles: options.ignoreFiles ?? [],
        crossLinks: options.crossLinks ?? [],
        groupBy: options.groupBy ?? "topic",
    };
}
