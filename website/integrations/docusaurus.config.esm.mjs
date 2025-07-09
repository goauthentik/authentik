/**
 * @file Docusaurus Integrations config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 */

import { createRequire } from "node:module";
import { resolve } from "node:path";
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
    staticDirectories: [
        // ---
        resolve(__dirname, "..", "static"),
        "static",
    ],

    themes: ["@goauthentik/docusaurus-theme"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        navbarReplacements: {
            INTEGRATIONS_URL: "/",
        },
        algolia: {
            externalUrlRegex: /^(?:https?:\/\/)(integrations|api).?(goauthentik.io)/.source,
        },
    }),

    plugins: [
        [
            "@docusaurus/theme-classic",
            {
                customCss: [
                    "./custom.css",
                    require.resolve("@goauthentik/docusaurus-config/css/index.css"),
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
                    routeBasePath: "/",
                    path: ".",
                    exclude: [...GlobExcludeDefault],
                    include: ["**/*.mdx", "**/*.md"],
                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/docs/integrations/",

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
    ],
};

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
