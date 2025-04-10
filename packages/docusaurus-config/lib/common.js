/**
 * @file Common Docusaurus configuration utilities.
 *
 * @import { Config as DocusaurusConfig } from "@docusaurus/types"
 * @import { UserThemeConfig } from "./theme.js"
 */

import { deepmerge } from "deepmerge-ts";
import { createThemeConfig } from "./theme.mjs";

//#region Types

/**
 * @typedef {Omit<DocusaurusConfig, 'themeConfig'>} DocusaurusConfigBase
 *
 * Represents the base configuration for Docusaurus, excluding the theme configuration.
 */

/**
 * @typedef DocusaurusConfigBaseTheme
 * @property {UserThemeConfig} themeConfig The theme configuration.
 *
 * Represents a configuration object, only including the theme configuration.
 */

/**
 * @typedef {Partial<DocusaurusConfigBase & DocusaurusConfigBaseTheme>} DocusaurusConfigInit
 *
 * The initial configuration for Docusaurus.
 *
 * @remarks
 * This type is the result of Docusaurs's less than ideal type definitions.
 * Much of the configuration is not strictly typed, however, this type
 * is a good starting point.
 */

//#endregion

//#region Functions

/**
 * Create a Docusaurus configuration.
 *
 * @param {DocusaurusConfigInit} [overrides] The options to override.
 * @returns {DocusaurusConfig}
 */
export function createDocusaurusConfig({ themeConfig, ...overrides } = {}) {
    /**
     * @type {DocusaurusConfig}
     */
    const config = {
        title: "authentik",
        tagline: "Bring all of your authentication into a unified platform.",
        url: "https://docs.goauthentik.io",
        baseUrl: "/",
        onBrokenLinks: "throw",
        onBrokenAnchors: "throw",
        favicon: "img/icon.png",
        organizationName: "Authentik Security Inc.",
        projectName: "authentik",
        markdown: {
            mermaid: true,
        },
        themeConfig: createThemeConfig(themeConfig),
    };

    return deepmerge(config, overrides);
}

//#endregion
