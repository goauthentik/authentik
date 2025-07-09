/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 */

import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { GlobExcludeDefault } from "@docusaurus/utils";
import { createApiPageMD } from "docusaurus-plugin-openapi-docs/lib/markdown/index.js";
import { gzip } from "pako";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

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
 * @satisfies {Partial<Config>}
 */
const config = {
    staticDirectories: [
        // ---
        "static",
        rootStaticDirectory,
    ],

    themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        navbarReplacements: {
            DOCS_URL: "/",
        },
        docs: {
            sidebar: {
                hideable: true,
            },
        },
    }),
    plugins: [
        [
            "@docusaurus/theme-classic",
            {
                customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
            },
        ],

        //#region Docs Content Plugin

        [
            "@docusaurus/plugin-content-docs",
            /** @type {DocsPluginOptions} */ ({
                showLastUpdateAuthor: false,
                showLastUpdateTime: false,
                numberPrefixParser: false,
                id: "docs",
                routeBasePath: "/",
                path: ".",
                exclude: [...GlobExcludeDefault],
                include: ["**/*.mdx", "**/*.md"],
                sidebarPath: "./sidebar.mjs",
                docItemComponent: "@theme/ApiItem",
                beforeDefaultRemarkPlugins: [
                    remarkLinkRewrite([
                        // ---
                        ["/integrations", "https://integrations.goauthentik.io"],
                        ["/docs", "https://docs.goauthentik.io"],
                    ]),
                ],
            }),
        ],

        //#endregion

        //#region OpenAPI Docs Plugin
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
                        template: "src/templates/api.mustache",
                        markdownGenerators: {
                            createApiPageMD: (pageData) => {
                                const {
                                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                                    info,
                                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                                    postman,
                                    ...coreAPI
                                } = pageData.api;

                                return [
                                    createApiPageMD(pageData),
                                    `export const api = "${btoa(
                                        String.fromCharCode(
                                            ...gzip(JSON.stringify(coreAPI), {
                                                level: 9,
                                            }),
                                        ),
                                    )}";`,
                                ].join("\n");
                            },
                        },
                    }),
                },
            },
        ],
    ],
    //#endregion
};

//#endregion

export default createDocusaurusConfig(config);
