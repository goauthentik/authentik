/**
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { AKMDXOnlyPluginOptions } from "./mdx-only/plugin.mjs";
 * @import { AKSearchPluginOptions } from "./search/plugin.mjs";
 * @import {Options as PresetOptions} from '@docusaurus/preset-classic';
 * @import { BuildUrlValues } from "remark-github";
 * @file Docusaurus config.
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
const production = process.env.NODE_ENV === "production";

export const DocusaurusExcludePatterns = [
    "**/_*.{js,jsx,ts,tsx,md,mdx}",
    "**/_*/**",
    "**/*.test.{js,jsx,ts,tsx}",
    "**/__tests__/**",
    "**/node_modules/**",
    // Build output lives under the docs root (path: ".") — never scan it as
    // content. The llms.txt plugin writes per-page `.md` into build/, so without
    // this a second build (with a dirty build/) ingests them as source and fails.
    "**/build/**",
    "**/out/**",
];

//#region Preset

/** @type {PresetOptions} */
const CommonPresetOptions = {
    ...(production
        ? {
              gtag: {
                  trackingID: "G-9MVR9WZFZH",
                  anonymizeIP: true,
              },
          }
        : {}),
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
 *
 * @returns {[string, PresetOptions]}
 */
export function createClassicPreset(overrides) {
    return ["@docusaurus/preset-classic", deepmerge(CommonPresetOptions, overrides)];
}

/**
 * Create the search plugin tuple. The plugin builds the self-hosted search index of every site
 * into this site's `static/search/` directory; `options.site` names the site being built.
 *
 * @param {AKSearchPluginOptions} options
 *
 * @returns {[string, AKSearchPluginOptions]}
 */
export function createSearchPlugin(options) {
    return ["@goauthentik/docusaurus-theme/search/plugin", options];
}

/**
 * Create the llms.txt plugin tuple.
 *
 * @param {import("./llms-txt/common.mjs").LLMSPluginOptions} options
 *
 * @returns {[string, import("./llms-txt/common.mjs").LLMSPluginOptions]}
 */
export function createLLMSPlugin(options) {
    return ["@goauthentik/docusaurus-theme/llms-txt/plugin", options];
}

/**
 * Create the MDX-only plugin tuple, which fails the build on `.md` content.
 *
 * @param {AKMDXOnlyPluginOptions} [options]
 *
 * @returns {[string, AKMDXOnlyPluginOptions]}
 */
export function createMDXOnlyPlugin(options) {
    return [
        "@goauthentik/docusaurus-theme/mdx-only/plugin",
        { ignore: DocusaurusExcludePatterns, ...options },
    ];
}

/**
 * Footer copyright line shared by every site.
 */
export const FOOTER_COPYRIGHT = `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`;

/**
 * @param {Partial<Config>} overrides
 *
 * @returns {Partial<Config>}
 */
export function extendConfig(overrides) {
    /**
     * @type {Partial<Config>}
     */
    const commonConfig = {
        plugins: [createMDXOnlyPlugin()],

        staticDirectories: [
            // ---
            resolve(__dirname, "..", "static"),
            "static",
        ],

        themeConfig: /** @type {Partial<UserThemeConfig>} */ ({
            footer: {
                copyright: FOOTER_COPYRIGHT,
            },
        }),
    };

    return deepmerge(commonConfig, overrides);
}
