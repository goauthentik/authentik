/**
 * @file Docusaurus Documentation config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { AKReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";
 */

import { cp } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { prepareReleaseEnvironment } from "@goauthentik/docusaurus-theme/releases/utils";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const rootStaticDirectory = resolve(__dirname, "..", "static");
const authentikModulePath = resolve(__dirname, "..", "..");

const releaseEnvironment = prepareReleaseEnvironment();

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

export default createDocusaurusConfig(
    extendConfig({
        future: {
            experimental_faster: true,
        },

        url: "https://docs.goauthentik.io",
        //#region Preset

        presets: [
            createClassicPreset({
                pages: false,
                docs: {
                    exclude: [
                        /**
                         * Exclude previously generated API docs.
                         *
                         * @expires 2025-12-01
                         */
                        "**/developer-docs/api/reference/**",
                    ],
                    routeBasePath: "/",
                    path: ".",

                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/docs/",

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            ["/api", "https://api.goauthentik.io"],
                            ["/integrations", "https://integrations.goauthentik.io"],
                        ]),
                    ],
                },
            }),
        ],

        //#endregion

        //#region Plugins

        plugins: [
            [
                "@goauthentik/docusaurus-theme/releases/plugin",
                /** @type {AKReleasesPluginOptions} */ ({
                    docsDirectory: __dirname,
                    environment: releaseEnvironment,
                }),
            ],
            [
                "@docusaurus/plugin-client-redirects",
                /** @type {RedirectsPluginOptions} */ ({
                    redirects: [
                        {
                            from: [
                                "/api",
                                "/docs/api",
                                "/docs/developer-docs/api/",
                                "/developer-docs/api/",
                            ],
                            to: releaseEnvironment.apiReferenceOrigin,
                        },
                    ],
                    createRedirects(existingPath) {
                        // Redirect to their respective path without the `docs/` prefix
                        return `/docs${existingPath}`;
                    },
                }),
            ],
        ],

        //#endregion

        //#region Theme

        themes: ["@goauthentik/docusaurus-theme", "@docusaurus/theme-mermaid"],

        themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
            algolia: createAlgoliaConfig({
                externalUrlRegex: /^(?:https?:\/\/)(?!docs\.goauthentik.io)/.source,
            }),

            image: "img/social.png",
            navbarReplacements: {
                DOCS_URL: "/",
            },
            navbar: {
                logo: {
                    alt: "authentik logo",
                    src: "img/icon_left_brand.svg",
                    href: "https://goauthentik.io/",
                    target: "_self",
                },
            },
        }),

        //#endregion
    }),
);
