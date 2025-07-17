/**
 * @file Docusaurus Documentation config.
 *
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { ReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 */

import { cp } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const rootStaticDirectory = resolve(__dirname, "..", "static");
const authentikModulePath = resolve(__dirname, "..", "..");

//#region Copy static files

const files = [
    // ---
    resolve(authentikModulePath, "docker-compose.yml"),
];

await Promise.all(
    files.map((file) => {
        const fileName = basename(file);
        const destPath = resolve(rootStaticDirectory, fileName);
        return cp(file, destPath, { recursive: true });
    }),
);

//#endregion

//#region Configuration

export default createDocusaurusConfig(
    extendConfig({
        future: {
            experimental_faster: true,
        },

        url: "https://docs.goauthentik.io",
        //#region Preset

        presets: [
            createClassicPreset({
                pages: {
                    path: "pages",
                },
                docs: {
                    routeBasePath: "/docs",
                    path: ".",

                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/docs/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            // TODO: Enable after base path is set to '/'
                            // ["/docs", ""],
                            ["/api", "https://api.goauthentik.io"],
                            ["/integrations", "https://integrations.goauthentik.io"],
                        ]),
                    ],
                },
            }),
        ],

        //#endregion

        //#region Plugins

        plugins: [
            [
                "@goauthentik/docusaurus-theme/releases/plugin",
                /** @type {ReleasesPluginOptions} */ ({
                    docsDirectory: __dirname,
                }),
            ],
        ],

        //#endregion

        //#region Theme

        themes: ["@goauthentik/docusaurus-theme", "@docusaurus/theme-mermaid"],

        themeConfig: /** @type {UserThemeConfig} */ ({
            algolia: createAlgoliaConfig({
                externalUrlRegex: /^(?:https?:\/\/)(?!docs\.goauthentik.io)/.source,
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
        }),

        //#endregion
    }),
);
