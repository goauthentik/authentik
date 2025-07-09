/**
 * @file Docusaurus Documentation config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import * as OpenAPIPlugin from "docusaurus-plugin-openapi-docs";
 * @import { UserThemeConfig } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { ReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 */
import { GlobExcludeDefault } from "@docusaurus/utils";
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";
import { deepmerge } from "deepmerge-ts";
import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);

const rootStaticDirectory = resolve(__dirname, "static");
const authentikModulePath = resolve(__dirname, "..");

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

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    themes: ["docusaurus-theme-openapi-docs", "@goauthentik/docusaurus-theme"],

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
    }),

    plugins: [
        [
            "@docusaurus/theme-classic",
            {
                customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
            },
        ],

        [
            "@goauthentik/docusaurus-theme/releases/plugin",
            /** @type {ReleasesPluginOptions} */ ({
                docsDirectory: __dirname,
            }),
        ],

        //#region Documentation

        [
            "@docusaurus/plugin-content-docs",
            deepmerge(
                CommonDocsPluginOptions,
                /** @type {DocsPluginOptions} */ ({
                    id: "docs",
                    routeBasePath: "/docs",
                    path: "docs",
                    exclude: [...GlobExcludeDefault],
                    include: ["**/*.mdx", "**/*.md"],

                    sidebarPath: "./docs/sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            // TODO: Enable after base path is set to '/'
                            // ["/docs", ""],
                            // TODO: Enable when API docs are ready
                            // ["/api", "https://api.goauthentik.io"],
                            ["/integrations", "https://integrations.goauthentik.io"],
                        ]),
                    ],
                }),
            ),
        ],

        [
            "docusaurus-plugin-openapi-docs",
            {
                id: "api",
                docsPluginId: "docs",
                config: /** @type {OpenAPIPlugin.Options} */ ({
                    authentik: {
                        specPath: "./static/schema.yml",
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
};

//#endregion

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
