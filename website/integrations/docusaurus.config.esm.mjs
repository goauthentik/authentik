/**
 * @file Docusaurus Integrations config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 */

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import categories from "./categories.mjs";
import { legacyRedirects } from "./legacy-redirects.mjs";

import { createDocusaurusConfig, DocusaurusURL } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    createLLMSPlugin,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { createRedirectPlugins } from "@goauthentik/docusaurus-theme/redirects/node";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const packageStaticDirectory = resolve(__dirname, "static");

const redirectPlugins = await createRedirectPlugins(resolve(packageStaticDirectory, "_redirects"), {
    redirects: Array.from(legacyRedirects, ([from, to]) => ({ from, to })),
});

//#region Configuration

export default createDocusaurusConfig(
    extendConfig({
        future: {
            faster: true,
        },

        url: DocusaurusURL.Integrations,

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
            createLLMSPlugin({
                sections: [{ path: ".", routeBasePath: "/" }],
                groupBy: "category",
                categories,
                // The integrations landing pages become an "## Overview" section
                // (inlined prose) instead of link rows; the scaffold template is dropped.
                overviewPages: ["index", "applications"],
                ignoreFiles: ["**/template/**"],
                crossLinks: [
                    {
                        label: "Documentation",
                        url: new URL("llms.txt", DocusaurusURL.Docs).toString(),
                    },
                ],
            }),

            ...redirectPlugins,
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
                    src: "https://goauthentik.io/img/icon_left_brand.svg",
                    href: "https://goauthentik.io/",
                    target: "_self",
                },
            },
        }),

        //#endregion
    }),
);
