/**
 * @file Docusaurus Integrations config.
 *
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";
 */

import { legacyRedirects } from "./legacy-redirects.mjs";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

//#region Configuration

export default createDocusaurusConfig(
    extendConfig({
        future: {
            experimental_faster: true,
        },

        url: "https://integrations.goauthentik.io",

        //#region Preset

        presets: [
            createClassicPreset({
                docs: {
                    path: ".",
                    routeBasePath: "/",
                    sidebarPath: "./sidebar.mjs",
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/integrations/",

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            ["/api", "https://api.goauthentik.io"],
                            ["/docs", "https://docs.goauthentik.io"],
                        ]),
                    ],
                },
            }),
        ],

        //#endregion

        //#region Plugins

        plugins: [
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

        //#endregion

        //#region Theme

        themes: ["@goauthentik/docusaurus-theme", "@docusaurus/theme-mermaid"],

        themeConfig: /** @type {UserThemeConfig} */ ({
            algolia: createAlgoliaConfig({
                externalUrlRegex: /^(?:https?:\/\/)(?!integrations\.goauthentik.io)/.source,
            }),
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
                        to: "/",
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
        }),

        //#endregion
    }),
);
