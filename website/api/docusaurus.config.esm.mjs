/**
 * @file Docusaurus config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { AKReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/plugin"
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 * @import {Options as PresetOptions} from '@docusaurus/preset-classic';
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";
 * @import { AKRedirectsPluginOptions } from "@goauthentik/docusaurus-theme/redirects/plugin"
 */

import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { RewriteIndex } from "@goauthentik/docusaurus-theme/redirects";
import { parse } from "@goauthentik/docusaurus-theme/redirects/node";
import { prepareReleaseEnvironment } from "@goauthentik/docusaurus-theme/releases/node";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);
const releaseEnvironment = prepareReleaseEnvironment();

const rootStaticDirectory = resolve(__dirname, "..", "static");
const authentikModulePath = resolve(__dirname, "..", "..");
const packageStaticDirectory = resolve(__dirname, "static");

const redirectsFile = resolve(packageStaticDirectory, "_redirects");
const redirects = await parse(redirectsFile);
const redirectsIndex = new RewriteIndex(redirects);

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
 */
export default createDocusaurusConfig({
    url: "https://api.goauthentik.io",

    staticDirectories: [
        // ---
        "static",
        rootStaticDirectory,
    ],

    //#region Preset

    presets: [
        [
            "@docusaurus/preset-classic",

            /** @type {PresetOptions} */ ({
                googleAnalytics: {
                    trackingID: "G-9MVR9WZFZH",
                    anonymizeIP: true,
                },
                theme: {
                    customCss: [require.resolve("@goauthentik/docusaurus-config/css/index.css")],
                },
                pages: false,
                docs: {
                    routeBasePath: "/",
                    path: ".",
                    docItemComponent: "@theme/ApiItem",

                    sidebarPath: "./sidebar.mjs",
                    showLastUpdateTime: false,
                    showLastUpdateAuthor: false,
                    numberPrefixParser: false,
                    exclude: [
                        "**/_*.{js,jsx,ts,tsx,md,mdx}",
                        "**/_*/**",
                        "**/*.test.{js,jsx,ts,tsx}",
                        "**/__tests__/**",
                        "**/node_modules/**",
                    ],
                    include: ["**/*.mdx", "**/*.md"],

                    //#region Docs Plugins

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            ["/integrations/", "https://integrations.goauthentik.io/"],
                            ["/docs/", "https://docs.goauthentik.io/docs/"],
                        ]),
                    ],
                },
            }),
        ],
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
                    }),
                },
            },
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

    themes: ["docusaurus-theme-openapi-docs"],

    themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
        footer: {
            copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
        },

        navbar: {
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
                href: "https://goauthentik.io/",
                target: "_self",
            },
        },

        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",

            externalUrlRegex: /^(?:https?:\/\/)(?!docs\.goauthentik.io)/.source,
        },
    }),

    //#endregion
});

//#endregion
