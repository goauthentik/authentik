/**
 * @file Docusaurus config.
 *
 * @import { BuildUrlValues } from "remark-github";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";

 */

import { createRequire } from "node:module";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";

import { GlobExcludeDefault } from "@docusaurus/utils";
import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

import remarkEnterpriseDirective from "../remark/enterprise-directive.mjs";
import remarkLinkRewrite from "../remark/link-rewrite-directive.mjs";
import remarkPreviewDirective from "../remark/preview-directive.mjs";
import remarkSupportDirective from "../remark/support-directive.mjs";
import remarkVersionDirective from "../remark/version-directive.mjs";
import { legacyRedirects } from "./legacy-redirects.mjs";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

/**
 * Documentation site configuration for Docusaurus.
 */
const config = createDocusaurusConfig({
    url: "https://integrations.goauthentik.io",
    future: {
        experimental_faster: true,
    },
    themes: ["@docusaurus/theme-mermaid"],
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
                },
                {
                    to: "https://docs.goauthentik.io",
                    label: "Documentation",
                    position: "left",
                    target: "_self",
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
            externalUrlRegex: /.*/.source,
        },
    },

    plugins: [
        [
            "@docusaurus/plugin-google-gtag",
            {
                trackingID: ["G-9MVR9WZFZH"],
                anonymizeIP: true,
            },
        ],

        [
            "@docusaurus/theme-classic",
            {
                customCss: [
                    require.resolve("@goauthentik/docusaurus-config/css/index.css"),
                    path.join(__dirname, "custom.css"),
                ],
            },
        ],

        [
            "@docusaurus/plugin-content-docs",
            /** @type {DocsPluginOptions} */ ({
                id: "docsIntegrations",
                exclude: [...GlobExcludeDefault],
                include: ["**/*.mdx", "**/*.md"],

                path: "integrations",
                routeBasePath: "/",
                sidebarPath: "./integrations/sidebar.mjs",
                editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
                showLastUpdateTime: false,

                beforeDefaultRemarkPlugins: [
                    remarkDirective,
                    remarkLinkRewrite(new Map([["/docs", "https://docs.goauthentik.io"]])),
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
            }),
        ],
        [
            "@docusaurus/plugin-client-redirects",
            /** @type {RedirectsPluginOptions} */ ({
                redirects: [
                    {
                        from: "/integrations",
                        to: "/",
                    },
                    ...Array.from(legacyRedirects, ([from, to]) => {
                        return {
                            from: [from, `/integrations${from}`],
                            to,
                        };
                    }),
                ],
            }),
        ],
    ],
});

export default config;
