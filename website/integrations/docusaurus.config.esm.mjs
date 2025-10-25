/**
 * @file Docusaurus Integrations config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { Options as RedirectsPluginOptions } from "@docusaurus/plugin-client-redirects";
 * @import { AKRedirectsPluginOptions } from "@goauthentik/docusaurus-theme/redirects/plugin"
 */

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { legacyRedirects } from "./legacy-redirects.mjs";

import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { RewriteIndex } from "@goauthentik/docusaurus-theme/redirects";
import { parse } from "@goauthentik/docusaurus-theme/redirects/node";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const packageStaticDirectory = resolve(__dirname, "static");

const redirectsFile = resolve(packageStaticDirectory, "_redirects");
const redirects = await parse(redirectsFile);
const redirectsIndex = new RewriteIndex(redirects);

//#region Configuration

export default createDocusaurusConfig(
    extendConfig({
        future: {
            experimental_faster: true,
        },

        url: "https://integrations.goauthentik.io",

        //#region Preset

        presets: [
            createClassicPreset({
                docs: {
                    path: ".",
                    routeBasePath: "/",
                    sidebarPath: "./sidebar.mjs",
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/integrations/",

                    beforeDefaultRemarkPlugins: [
                        remarkLinkRewrite([
                            // ---
                            ["/api", "https://api.goauthentik.io"],
                            ["/docs", "https://docs.goauthentik.io"],
                        ]),
                    ],
                },
            }),
        ],

        //#endregion

        //#region Plugins

        plugins: [
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
                    redirects: Array.from(legacyRedirects, ([from, to]) => {
                        return {
                            from,
                            to,
                        };
                    }),
                }),
            ],
        ],

        //#endregion

        //#region Theme

        themes: ["@goauthentik/docusaurus-theme", "@docusaurus/theme-mermaid"],

        themeConfig: /** @type {UserThemeConfig & UserThemeConfigExtra} */ ({
            algolia: createAlgoliaConfig({
                externalUrlRegex: /^(?:https?:\/\/)(?!integrations\.goauthentik.io)/.source,
            }),
            image: "img/social.png",
            navbarReplacements: {
                INTEGRATIONS_URL: "/",
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
