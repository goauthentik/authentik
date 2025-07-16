/**
 * @file Docusaurus Integrations config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { BuildUrlValues } from "remark-github";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";
 */

import { createRequire } from "node:module";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { GlobExcludeDefault } from "@docusaurus/utils";
import { deepmerge } from "deepmerge-ts";

import { legacyRedirects } from "./legacy-redirects.mjs";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    url: "https://integrations.goauthentik.io",
    future: {
        experimental_faster: true,
    },
    themes: ["@goauthentik/docusaurus-theme", "@docusaurus/theme-mermaid"],
    themeConfig: /** @type {UserThemeConfig} */ ({
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
    }),

    plugins: [
        [
            "@docusaurus/theme-classic",
            {
                customCss: [
                    require.resolve("@goauthentik/docusaurus-config/css/index.css"),
                    join(__dirname, "./custom.css"),
                ],
            },
        ],

        //#region Documentation

        [
            "@docusaurus/plugin-content-docs",
            deepmerge(
                CommonDocsPluginOptions,
                /** @type {DocsPluginOptions} */ ({
                    id: "docsIntegrations",
                    exclude: [...GlobExcludeDefault],
                    include: ["**/*.mdx", "**/*.md"],

                    path: "integrations",
                    routeBasePath: "/",
                    sidebarPath: "./integrations/sidebar.mjs",
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
                    showLastUpdateTime: false,
                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            ["/api", "https://api.goauthentik.io"],
                            ["/docs", "https://docs.goauthentik.io"],
                        ]),
                    ],
                }),
            ),
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
        ["@docusaurus/plugin-sitemap", {}],
    ],
};

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
