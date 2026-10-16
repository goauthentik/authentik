/**
 * @import { UserThemeConfig as UserThemeConfigCommon } from "@docusaurus/theme-common";
 *
 * @import {NavbarItemOverrides} from "./navbar.js"
 * @file Docusaurus theme configuration for the authentik website.
 */

import { createNavbarItems } from "./navbar.js";

import { deepmerge } from "deepmerge-ts";
import { themes as prismThemes } from "prism-react-renderer";

//#region Types

/**
 * @typedef {Object} UserThemeConfigExtra
 * @property {Partial<NavbarItemOverrides>} [navbarReplacements] The replacements for the navbar.
 */

/**
 * Theme configuration for Docusaurus.
 *
 * @typedef {UserThemeConfigCommon} UserThemeConfig
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
 * @param {Partial<UserThemeConfigCommon['prism']>} overrides - Overrides for the default Prisma
 *   configuration.
 *
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
            "powershell",
        ],
    };

    return deepmerge(prismConfig, overrides);
}

/**
 * Creates a theme configuration for Docusaurus.
 *
 * @param {Partial<UserThemeConfig & UserThemeConfigExtra>} overrides - Overrides for the default
 *   theme configuration.
 *
 * @returns {UserThemeConfig}
 */
export function createThemeConfig({ prism, navbarReplacements, ...overrides } = {}) {
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
        footer: {
            copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
        },
        navbar: {
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
            },

            items: createNavbarItems(navbarReplacements),
        },
        prism: createPrismConfig(prism),
    };

    return deepmerge(themeConfig, overrides);
}
