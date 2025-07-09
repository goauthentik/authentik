/**
 * @file Docusaurus Integrations config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 */

import { createRequire } from "node:module";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { GlobExcludeDefault } from "@docusaurus/utils";
import { deepmerge } from "deepmerge-ts";

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
    themes: ["@goauthentik/docusaurus-theme"],
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
                    to: "integrations/",
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
                    id: "docs",
                    routeBasePath: "/integrations",
                    path: "integrations",
                    exclude: [...GlobExcludeDefault],
                    include: ["**/*.mdx", "**/*.md"],
                    sidebarPath: "./integrations/sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/docs/integrations/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            // TODO: Enable when API docs are ready
                            // ["/api", "https://api.goauthentik.io"],
                            ["/docs", "https://docs.goauthentik.io"],
                        ]),
                    ],
                }),
            ),
        ],
    ],
};

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
