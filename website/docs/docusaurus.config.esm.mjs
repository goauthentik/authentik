/**
 * @file Docusaurus Documentation config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { AKReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 * @import { AKRedirectsPluginOptions } from "@goauthentik/docusaurus-theme/redirects/plugin"
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
import { RewriteIndex } from "@goauthentik/docusaurus-theme/redirects";
import { parse } from "@goauthentik/docusaurus-theme/redirects/node";
import { prepareReleaseEnvironment } from "@goauthentik/docusaurus-theme/releases/node";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const rootStaticDirectory = resolve(__dirname, "..", "static");
const packageStaticDirectory = resolve(__dirname, "static");
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

const redirectsFile = resolve(packageStaticDirectory, "_redirects");
const redirects = await parse(redirectsFile);
const redirectsIndex = new RewriteIndex(redirects);

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

            // Inject redirects for later use during runtime,
            // such as navigating to non-existent page with the client-side router.

            [
                "@goauthentik/docusaurus-theme/redirects/plugin",
                /** @type {AKRedirectsPluginOptions} */ ({
                    redirects,
                }),
            ],

            // Create build-time redirects for later use in HTTP responses,
            // such as when navigating to a page for the first time.
            //
            // The existence of the _redirects file is also picked up by
            // Netlify's deployment, which will redirect to the correct URL, even
            // if the source is no longer present within the build output,
            // such as when a page is removed, renamed, or moved.
            [
                "@docusaurus/plugin-client-redirects",
                /** @type {RedirectsPluginOptions} */ ({
                    createRedirects(existingPath) {
                        const redirects = redirectsIndex.findAliases(existingPath);

                        return redirects;
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
