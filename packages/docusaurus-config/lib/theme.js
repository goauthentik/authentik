/**
 * @file Docusaurus theme configuration for the authentik website.
 *
 * @import { UserThemeConfig as UserThemeConfigCommon } from "@docusaurus/theme-common";
 * @import { UserThemeConfig as UserThemeConfigAlgolia } from "@docusaurus/theme-search-algolia";
 */

import { deepmerge } from "deepmerge-ts";
import { themes as prismThemes } from "prism-react-renderer";

//#region Types

/**
 * Combined theme configuration for Docusaurus and Algolia.
 *
 * @typedef {UserThemeConfigCommon & UserThemeConfigAlgolia} UserThemeConfig
 */

//#endregion

//#region Functions

/**
 * @returns {string} The copyright string.
 */
export function formatCopyright() {
    return `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`;
}

/**
 * Creates a Prisma configuration for Docusaurus.
 *
 * @param {Partial<UserThemeConfigCommon['prism']>} overrides - Overrides for the default Prisma configuration.
 * @returns {UserThemeConfigCommon['prism']}
 */
export function createPrismConfig(overrides = {}) {
    /**
     * @type {UserThemeConfigCommon['prism']}
     */
    const prismConfig = {
        theme: prismThemes.oneLight,
        darkTheme: prismThemes.oneDark,
        additionalLanguages: [
            // ---
            "apacheconf",
            "diff",
            "http",
            "json",
            "nginx",
            "python",
            "bash",
        ],
    };

    return deepmerge(prismConfig, overrides);
}

/**
 * Creates a theme configuration for Docusaurus.
 *
 * @param {Partial<UserThemeConfig>} overrides - Overrides for the default theme configuration.
 * @returns {UserThemeConfig}
 */
export function createThemeConfig({ prism, ...overrides } = {}) {
    /**
     * @type {UserThemeConfig}
     */
    const themeConfig = {
        image: "img/social.png",
        tableOfContents: {
            minHeadingLevel: 2,
            maxHeadingLevel: 3,
        },
        colorMode: {
            respectPrefersColorScheme: true,
        },
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
        },
        prism: createPrismConfig(prism),
    };

    return deepmerge(themeConfig, overrides);
}
