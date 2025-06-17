/**
 * @file Docusaurus Documentation config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { ReleasesPluginOptions } from "./releases/plugin.mjs"
 */
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { deepmerge } from "deepmerge-ts";
import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);
const staticDirectory = resolve(__dirname, "static");

//#region Copy static files

const authentikModulePath = resolve("..");

await Promise.all([
    cp(
        resolve(authentikModulePath, "docker-compose.yml"),
        resolve(staticDirectory, "docker-compose.yml"),
    ),
    cp(resolve(authentikModulePath, "schema.yml"), resolve(staticDirectory, "schema.yml")),
]);

//#endregion

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    themes: ["@goauthentik/docusaurus-theme"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        navbarReplacements: {
            DOCS_URL: "/",
        },
        algolia: {
            externalUrlRegex: /^(?:https?:\/\/)(integrations|api).?(goauthentik.io)/.source,
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
            "./releases/plugin.mjs",
            /** @type {ReleasesPluginOptions} */ ({
                docsDirectory: join(__dirname, "articles"),
            }),
        ],

        //#region Documentation

        [
            "@docusaurus/plugin-content-docs",
            deepmerge(
                CommonDocsPluginOptions,
                /** @type {DocsPluginOptions} */ ({
                    id: "docs",
                    routeBasePath: "/",
                    path: "articles",
                    sidebarPath: "./articles/sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/docs/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            ["/docs", "/articles"],
                            ["/api", "https://api.goauthentik.io"],
                            ["/integrations", "https://integrations.goauthentik.io"],
                        ]),
                    ],
                }),
            ),
        ],
    ],
};

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
