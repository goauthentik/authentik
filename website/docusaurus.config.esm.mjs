/**
 * @file Docusaurus config.
 *
 * @import { Config } from "@docusaurus/types";
 * @import { UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as DocsPluginOptions } from "@docusaurus/plugin-content-docs";
 * @import * as Preset from "@docusaurus/preset-classic";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 * @import { BuildUrlValues } from "remark-github";
 * @import { ReleasesPluginOptions } from "./releases/plugin.mjs"
 */
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";

import remarkNPM2Yarn from "@docusaurus/remark-plugin-npm2yarn";
import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

import {
    remarkEnterpriseDirective,
    remarkLinkRewrite,
    remarkPreviewDirective,
    remarkSupportDirective,
    remarkVersionDirective,
} from "./remark/index.mjs";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));
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
    url: "https://docs.goauthentik.io",
    themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],
    themeConfig: /** @type {UserThemeConfigExtra} */ ({
        navbarReplacements: {
            DOCS_URL: "/",
        },
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",
            externalUrlRegex: new RegExp(
                "(:\\/\\/goauthentik\\.io|integrations\\.goauthentik\\.io)",
            ).toString(),
        },
    }),
    presets: Date.now()
        ? []
        : [
              //#region Presets

              [
                  "@docusaurus/preset-classic",
                  /** @type {Preset.Options} */ ({
                      theme: {
                          customCss: require.resolve(
                              "@goauthentik/docusaurus-config/css/index.css",
                          ),
                      },

                      docs: {
                          id: "docs",
                          routeBasePath: "/",
                          path: "docs",
                          sidebarPath: "./docs/sidebar.mjs",
                          showLastUpdateTime: false,
                          editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",

                          //#region Docs Plugins

                          beforeDefaultRemarkPlugins: [
                              remarkDirective,
                              remarkLinkRewrite([
                                  // ---
                                  ["/integrations", "https://integrations.goauthentik.io"],
                              ]),
                              remarkVersionDirective,
                              remarkEnterpriseDirective,
                              remarkPreviewDirective,
                              remarkSupportDirective,
                          ],

                          remarkPlugins: [
                              [remarkNPM2Yarn, { sync: true }],
                              [
                                  remarkGithub,
                                  {
                                      repository: "goauthentik/authentik",
                                      /**
                                       * @param {BuildUrlValues} values
                                       */
                                      buildUrl: (values) => {
                                          // Only replace issues and PR links
                                          return values.type === "issue" ||
                                              values.type === "mention"
                                              ? defaultBuildUrl(values)
                                              : false;
                                      },
                                  },
                              ],
                          ],

                          //#endregion
                      },
                  }),
              ],

              //#endregion
          ],
    plugins: [
        [
            "./releases/plugin.mjs",
            /** @type {ReleasesPluginOptions} */ ({
                docsDirectory: join(__dirname, "docs"),
            }),
        ],

        [
            "@docusaurus/theme-classic",
            {
                customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
            },
        ],

        //#region API Docs
        [
            "@docusaurus/plugin-content-docs",
            /** @type {DocsPluginOptions} */ ({
                id: "api",
                path: "api",
                routeBasePath: "api",
                sidebarPath: "api/sidebar.mjs",
                docItemComponent: "@theme/ApiItem",
                remarkPlugins: [
                    // ---
                    [remarkNPM2Yarn, { sync: true }],
                ],
                editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
            }),
        ],
        [
            "docusaurus-plugin-openapi-docs",
            {
                id: "open-api-docs",
                docsPluginId: "api",
                config: {
                    authentik: /** @type {OpenApiPlugin.Options} */ ({
                        specPath: "static/schema.yml",
                        outputDir: "api/reference",
                        hideSendButton: true,
                        sidebarOptions: {
                            groupPathsBy: "tag",
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
