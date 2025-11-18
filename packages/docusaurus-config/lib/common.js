/**
 * @file Common Docusaurus configuration utilities.
 *
 * @import { Config, DocusaurusConfig } from "@docusaurus/types"
 * @import { UserThemeConfig, UserThemeConfigExtra } from "./theme.js"
 */

import { createThemeConfig } from "./theme.js";

import { deepmerge } from "deepmerge-ts";

//#region Types

/**
 * @typedef {Omit<Config, 'themeConfig'>} DocusaurusConfigBase
 *
 * Represents the base configuration for Docusaurus, excluding the theme configuration.
 */

/**
 * @typedef DocusaurusConfigBaseTheme
 * @property {UserThemeConfig & UserThemeConfigExtra} themeConfig The theme configuration.
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
 * Create a default Docusaurus configuration.
 */
export function createDefaultDocusaurusConfig() {
    const NodeEnvironment = process.env.AK_DOCUSAURUS_ENV || process.env.NODE_ENV || "development";
    const production = NodeEnvironment === "production";

    /**
     * @satisfies {Config}
     */
    const DEFAULT_CONFIG = /** @type {const} */ ({
        trailingSlash: true,
        future: {
            v4: {
                removeLegacyPostBuildHeadAttribute: true,
                useCssCascadeLayers: false,
            },
            experimental_faster: {
                swcJsLoader: true,
                rspackBundler: true,
                lightningCssMinimizer: production,
                swcJsMinimizer: production,
                swcHtmlMinimizer: production,
                ssgWorkerThreads: production,
                mdxCrossCompilerCache: production,
                rspackPersistentCache: production,
            },
        },

        title: "authentik",
        tagline: "Bring all of your authentication into a unified platform.",
        url: "https://docs.goauthentik.io",
        baseUrl: "/",
        onBrokenLinks: "throw",
        onBrokenAnchors: "throw",
        onDuplicateRoutes: "throw",
        favicon: "img/icon.png",
        organizationName: "Authentik Security Inc.",
        projectName: "authentik",
        markdown: {
            mermaid: true,
            hooks: {
                onBrokenMarkdownLinks: "throw",
                onBrokenMarkdownImages: "throw",
            },
        },
    });

    return DEFAULT_CONFIG;
}

/**
 * Create a Docusaurus configuration.
 *
 * @template {Partial<Config>} T
 * @param {T} overrides The options to override.
 * @returns {T & ReturnType<typeof createDefaultDocusaurusConfig>}
 */
export function createDocusaurusConfig({ themeConfig, ...overrides }) {
    const config = {
        ...createDefaultDocusaurusConfig(),
        themeConfig: createThemeConfig(themeConfig),
    };

    // @ts-ignore
    return deepmerge(config, overrides);
}

//#endregion
