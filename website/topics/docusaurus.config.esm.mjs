/**
 * @file Docusaurus Documentation config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import { ReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 */

import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { CommonConfig, CommonDocsPluginOptions } from "@goauthentik/docusaurus-theme/config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { GlobExcludeDefault } from "@docusaurus/utils";
import { deepmerge } from "deepmerge-ts";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);

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

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    staticDirectories: [
        // ---
        rootStaticDirectory,
        "static",
    ],

    themes: ["@goauthentik/docusaurus-theme"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        navbarReplacements: {
            DOCS_URL: "/",
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
                    routeBasePath: "/",
                    path: ".",
                    exclude: [...GlobExcludeDefault],
                    include: ["**/*.mdx", "**/*.md"],

                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            ["/docs", ""],
                            ["/api", "https://api.goauthentik.io"],
                            ["/integrations", "https://integrations.goauthentik.io"],
                        ]),
                    ],
                }),
            ),
        ],
    ],
};

//#endregion

export default /** @type {Config} */ (deepmerge(CommonConfig, createDocusaurusConfig(config)));
