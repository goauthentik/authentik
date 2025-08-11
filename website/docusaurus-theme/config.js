/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import {Options as PresetOptions} from '@docusaurus/preset-classic';
 * @import { BuildUrlValues } from "remark-github";
 */

import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
    remarkEnterpriseDirective,
    remarkPreviewDirective,
    remarkSupportDirective,
    remarkVersionDirective,
} from "#remark";

import { deepmerge } from "deepmerge-ts";
import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

export const DocusaurusExcludePatterns = [
    "**/_*.{js,jsx,ts,tsx,md,mdx}",
    "**/_*/**",
    "**/*.test.{js,jsx,ts,tsx}",
    "**/__tests__/**",
    "**/node_modules/**",
];

//#region Preset

/** @type {PresetOptions} */
const CommonPresetOptions = {
    googleAnalytics: {
        trackingID: "G-9MVR9WZFZH",
        anonymizeIP: true,
    },
    theme: {
        customCss: [require.resolve("@goauthentik/docusaurus-config/css/index.css")],
    },

    docs: {
        showLastUpdateTime: false,
        exclude: DocusaurusExcludePatterns,
        include: ["**/*.mdx", "**/*.md"],

        //#region Docs Plugins

        beforeDefaultRemarkPlugins: [
            remarkDirective,
            remarkVersionDirective,
            remarkEnterpriseDirective,
            remarkPreviewDirective,
            remarkSupportDirective,
        ],

        remarkPlugins: [
            [
                remarkGithub,
                {
                    repository: "goauthentik/authentik",
                    /**
                     * @param {BuildUrlValues} values
                     */
                    buildUrl: (values) => {
                        // Only replace issues and PR links
                        return values.type === "issue" || values.type === "mention"
                            ? defaultBuildUrl(values)
                            : false;
                    },
                },
            ],
        ],

        //#endregion
    },
};

//#endregion

/**
 * @param {Partial<PresetOptions>} overrides
 * @returns {[string, PresetOptions]}
 */
export function createClassicPreset(overrides) {
    return ["@docusaurus/preset-classic", deepmerge(CommonPresetOptions, overrides)];
}

/**
 *
 * @param {Partial<UserThemeConfig["algolia"]>} [overrides]
 * @returns {UserThemeConfig["algolia"]}
 */
export function createAlgoliaConfig(overrides) {
    return {
        appId: "36ROD0O0FV",
        apiKey: "727db511300ca9aec5425645bbbddfb5",
        indexName: "goauthentik",
        externalUrlRegex: /.*/.source,
        ...overrides,
    };
}

/**
 * @param {Partial<Config>} overrides
 * @returns {Partial<Config>}
 */
export function extendConfig(overrides) {
    /**
     * @type {Partial<Config>}
     */
    const commonConfig = {
        staticDirectories: [
            // ---
            resolve(__dirname, "..", "static"),
            "static",
        ],

        themeConfig: /** @type {Partial<UserThemeConfig>} */ ({
            footer: {
                copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
            },
        }),
    };

    return deepmerge(commonConfig, overrides);
}
