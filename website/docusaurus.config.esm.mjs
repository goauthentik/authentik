/**
 * @file Docusaurus config.
 *
 * @import * as Preset from "@docusaurus/preset-classic";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 * @import { BuildUrlValues } from "remark-github";
 */

import { createRequire } from "node:module";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";

import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

import remarkEnterpriseDirective from "./remark/enterprise-directive.mjs";
import remarkLinkRewrite from "./remark/link-rewrite-directive.mjs";
import remarkPreviewDirective from "./remark/preview-directive.mjs";
import remarkSupportDirective from "./remark/support-directive.mjs";
import remarkVersionDirective from "./remark/version-directive.mjs";

const require = createRequire(import.meta.url);

/**
 * Documentation site configuration for Docusaurus.
 */
const config = createDocusaurusConfig({
    url: "https://docs.goauthentik.io",
    future: {
        experimental_faster: true,
    },
    themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],
    themeConfig: {
        image: "img/social.png",
        navbar: {
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
                href: "https://goauthentik.io/",
                target: "_self",
            },
            items: [
                {
                    to: "https://goauthentik.io/features",
                    label: "Features",
                    position: "left",
                    target: "_self",
                },
                {
                    to: "https://integrations.goauthentik.io",
                    label: "Integrations",
                    position: "left",
                    target: "_self",
                },
                {
                    to: "docs/",
                    label: "Documentation",
                    position: "left",
                },
                {
                    to: "https://goauthentik.io/pricing/",
                    label: "Pricing",
                    position: "left",
                    target: "_self",
                },
                {
                    to: "https://goauthentik.io/blog",
                    label: "Blog",
                    position: "left",
                    target: "_self",
                },
                {
                    "href": "https://github.com/goauthentik/authentik",
                    "data-icon": "github",
                    "aria-label": "GitHub",
                    "position": "right",
                },
                {
                    "href": "https://goauthentik.io/discord",
                    "data-icon": "discord",
                    "aria-label": "Discord",
                    "position": "right",
                },
            ],
        },
        footer: {
            links: [],
            copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
        },
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",
            externalUrlRegex: /(:\/\/goauthentik\.io|integrations\.goauthentik\.io)/.toString(),
        },
    },
    presets: [
        [
            "@docusaurus/preset-classic",
            /** @type {Preset.Options} */ ({
                docs: {
                    id: "docs",
                    routeBasePath: "docs",
                    sidebarPath: "./sidebars/docs.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
                    docItemComponent: "@theme/ApiItem",

                    beforeDefaultRemarkPlugins: [
                        remarkDirective,
                        remarkLinkRewrite(
                            new Map([["/integrations", "https://integrations.goauthentik.io"]]),
                        ),
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
                },
                gtag: {
                    trackingID: ["G-9MVR9WZFZH"],
                    anonymizeIP: true,
                },
                theme: {
                    customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
                },
            }),
        ],
    ],
    plugins: [
        [
            "docusaurus-plugin-openapi-docs",
            {
                id: "api",
                docsPluginId: "docs",
                config: /** @type {OpenApiPlugin.Options} */ ({
                    authentik: {
                        specPath: "static/schema.yml",
                        outputDir: "docs/developer-docs/api/reference/",
                        hideSendButton: true,
                        sidebarOptions: {
                            groupPathsBy: "tag",
                        },
                    },
                }),
            },
        ],
    ],
});

export default config;
