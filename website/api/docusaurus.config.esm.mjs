/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 */
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

import { createApiPageMD } from "docusaurus-plugin-openapi-docs/lib/markdown/index.js";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzip } from "pako";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

const rootStaticDirectory = resolve(__dirname, "..", "static");

//#region Configuration

/**
 * Documentation site configuration for Docusaurus.
 * @satisfies {Partial<Config>}
 */
const config = {
    themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],
    staticDirectories: [
        // ---
        "static",
        rootStaticDirectory,
    ],

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
                numberPrefixParser: false,
                id: "docs",
                path: "articles",
                routeBasePath: "/",
                sidebarPath: "./articles/sidebar.mjs",
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
                        specPath: resolve(rootStaticDirectory, "schema.yml"),
                        outputDir: "articles/reference",
                        hideSendButton: true,
                        disableCompression: true,
                        sidebarOptions: {
                            groupPathsBy: "tag",
                        },
                        template: "templates/api.mustache",
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
