/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { BuildUrlValues } from "remark-github";
 */

import {
    remarkEnterpriseDirective,
    remarkPreviewDirective,
    remarkSupportDirective,
    remarkVersionDirective,
} from "#remark";

import remarkNPM2Yarn from "@docusaurus/remark-plugin-npm2yarn";
import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

//#region Common configuration

/**
 * @satisfies {DocsPluginOptions}
 */
export const CommonDocsPluginOptions = {
    id: "docs",
    routeBasePath: "/",
    path: "docs",
    sidebarPath: "./docs/sidebar.mjs",
    showLastUpdateTime: false,
    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",

    //#region Docs Plugins

    beforeDefaultRemarkPlugins: [
        remarkDirective,
        remarkVersionDirective,
        remarkEnterpriseDirective,
        remarkPreviewDirective,
        remarkSupportDirective,
    ],

    remarkPlugins: [
        [remarkNPM2Yarn, { sync: true }],
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
};

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
export const CommonConfig = {
    themes: ["@docusaurus/theme-mermaid"],
    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",
            externalUrlRegex: /.*/.source,
        },
    }),
    plugins: [
        [
            "@docusaurus/plugin-google-gtag",
            {
                trackingID: ["G-9MVR9WZFZH"],
                anonymizeIP: true,
            },
        ],
    ],
};
