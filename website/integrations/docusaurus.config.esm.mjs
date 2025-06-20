/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import * as Preset from "@docusaurus/preset-classic";
 */
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";

import { createRequire } from "node:module";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import remarkDirective from "remark-directive";

import {
    remarkEnterpriseDirective,
    remarkLinkRewrite,
    remarkPreviewDirective,
    remarkSupportDirective,
    remarkVersionDirective,
} from "../remark/index.mjs";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

//#region Docs Plugins

const beforeDefaultRemarkPlugins = [
    remarkDirective,
    remarkLinkRewrite([
        // ---
        ["/docs", "https://docs.goauthentik.io"],
    ]),
    remarkVersionDirective,
    remarkEnterpriseDirective,
    remarkPreviewDirective,
    remarkSupportDirective,
];

//#endregion

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    url: "https://integrations.goauthentik.io",
    themes: ["@docusaurus/theme-mermaid"],
    themeConfig: /** @type {UserThemeConfigExtra} */ ({
        navbarReplacements: {
            INTEGRATIONS_URL: "/",
        },
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",
            externalUrlRegex: /(:\/\/goauthentik\.io|docs\.goauthentik\.io)/.toString(),
        },
    }),
    presets: [
        //#region Presets

        [
            "@docusaurus/preset-classic",
            /** @type {Preset.Options} */ ({
                theme: {
                    customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
                },

                docs: {
                    // include: [
                    //     // ---
                    //     __dirname,
                    //     path.join(__dirname, "**/*"),
                    // ],
                    exclude: [
                        path.resolve(__dirname, "..", "api", "**/*"),
                        path.resolve(__dirname, "..", "docs", "**/*"),
                    ],
                    id: "integrations",
                    path: "integrations",
                    routeBasePath: "/",
                    sidebarPath: "./integrations/sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
                    beforeDefaultRemarkPlugins,
                },
            }),
        ],

        //#endregion
    ],

    //#endregion
};

//#endregion

export default createDocusaurusConfig(config);
