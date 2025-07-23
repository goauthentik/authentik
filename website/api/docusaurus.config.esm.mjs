/**
 * @file Docusaurus config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 * @import {Options as PresetOptions} from '@docusaurus/preset-classic';
 */

import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);

const rootStaticDirectory = resolve(__dirname, "..", "static");
const authentikModulePath = resolve(__dirname, "..", "..");

//#region Copy static files

const files = [
    // ---
    resolve(authentikModulePath, "schema.yml"),
];

await Promise.all(
    files.map((file) => {
        const fileName = basename(file);
        const destPath = resolve(rootStaticDirectory, fileName);
        return cp(file, destPath, {
            recursive: true,
        });
    }),
);

//#endregion

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 */
export default createDocusaurusConfig({
    url: "https://api.goauthentik.io",

    staticDirectories: [
        // ---
        "static",
        rootStaticDirectory,
    ],

    //#region Preset

    presets: [
        [
            "@docusaurus/preset-classic",

            /** @type {PresetOptions} */ ({
                googleAnalytics: {
                    trackingID: "G-9MVR9WZFZH",
                    anonymizeIP: true,
                },
                theme: {
                    customCss: [require.resolve("@goauthentik/docusaurus-config/css/index.css")],
                },
                docs: {
                    routeBasePath: "/",
                    path: ".",
                    docItemComponent: "@theme/ApiItem",

                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    showLastUpdateAuthor: false,
                    numberPrefixParser: false,
                    exclude: [
                        "**/_*.{js,jsx,ts,tsx,md,mdx}",
                        "**/_*/**",
                        "**/*.test.{js,jsx,ts,tsx}",
                        "**/__tests__/**",
                        "**/node_modules/**",
                    ],
                    include: ["**/*.mdx", "**/*.md"],

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            ["/integrations/", "https://integrations.goauthentik.io/"],
                            ["/docs/", "https://docs.goauthentik.io/docs/"],
                        ]),
                    ],
                },
            }),
        ],
    ],

    //#endregion

    //#region Plugins

    plugins: [
        [
            "docusaurus-plugin-openapi-docs",
            {
                id: "open-api-docs",
                docsPluginId: "docs",
                config: {
                    authentik: /** @type {OpenApiPlugin.Options} */ ({
                        specPath: resolve("..", "..", "schema.yml"),
                        outputDir: "./reference",
                        hideSendButton: true,
                        disableCompression: true,
                        sidebarOptions: {
                            groupPathsBy: "tag",
                        },
                    }),
                },
            },
        ],
    ],

    //#endregion

    //#region Theme

    themes: ["docusaurus-theme-openapi-docs"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        footer: {
            copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
        },

        navbar: {
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
                href: "https://goauthentik.io/",
                target: "_self",
            },
        },

        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",

            externalUrlRegex: /^(?:https?:\/\/)(?!docs\.goauthentik.io)/.source,
        },
    }),

    //#endregion
});

//#endregion
