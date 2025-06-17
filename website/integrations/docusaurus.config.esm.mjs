/**
 * @file Docusaurus Integrations config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 */
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { deepmerge } from "deepmerge-ts";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    themes: ["@goauthentik/docusaurus-theme"],
    staticDirectories: [
        // ---
        resolve(__dirname, "..", "static"),
        "static",
    ],

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
                customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
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
                    path: "articles",
                    sidebarPath: "./articles/sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/docs/integrations/",

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
