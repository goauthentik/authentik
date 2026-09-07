/**
 * @file Common Docusaurus configuration utilities.
 *
 * @import { Config } from "@docusaurus/types"
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
 * @typedef {Partial<DocusaurusConfigBaseTheme> & Record<string, unknown>} DocusaurusConfigInit
 *
 * The initial configuration for Docusaurus.
 *
 * @remarks
 * This type is intentionally loose: it references the theme config we care about
 * but keeps the remaining fields as a plain index signature rather than
 * `Partial<Config>`. Consumers (the website site configs) resolve their own copy
 * of `@docusaurus/types`, and comparing two peer-resolved `Config` instances
 * structurally overflows the type checker (TS2321). Keeping this type free of
 * `Config` avoids that cross-package comparison at the call boundary.
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
            faster: {
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
 * @param {DocusaurusConfigInit} overrides The options to override.
 * @returns {Config}
 */
export function createDocusaurusConfig({ themeConfig, ...overrides }) {
    const config = {
        ...createDefaultDocusaurusConfig(),
        themeConfig: createThemeConfig(themeConfig),
    };

    const merged = /** @type {Config} */ (deepmerge(config, overrides));

    // Declare the site name for search engines. Without an explicit `WebSite`
    // structured-data `name`, Google synthesizes the site name from the hostname
    // and renders it title-cased ("Authentik"); the product name is always
    // lowercase. https://developers.google.com/search/docs/appearance/site-names
    merged.headTags = [
        ...(merged.headTags ?? []),
        {
            tagName: "script",
            attributes: { type: "application/ld+json" },
            innerHTML: JSON.stringify({
                "@context": "https://schema.org",
                "@type": "WebSite",
                name: "authentik",
                url: `${merged.url}${merged.baseUrl}`,
            }),
        },
    ];

    return merged;
}

//#endregion
