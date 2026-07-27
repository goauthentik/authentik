/**
 * @file Docusaurus Documentation config.
 *
 * @import { UserThemeConfig, UserThemeConfigExtra } from "@goauthentik/docusaurus-config";
 * @import { AKReleasesPluginOptions } from "@goauthentik/docusaurus-theme/releases/common"
 * @import { NormalizedSidebar, NormalizedSidebarItemCategory, SidebarItemsGeneratorArgs } from "@docusaurus/plugin-content-docs/src/sidebars/types.ts";
 */

import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import topics from "./topics.mjs";

import { createDocusaurusConfig, DocusaurusURL } from "@goauthentik/docusaurus-config";
import {
    createAlgoliaConfig,
    createClassicPreset,
    createLLMSPlugin,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
import { createRedirectPlugins } from "@goauthentik/docusaurus-theme/redirects/node";
import { prepareReleaseEnvironment } from "@goauthentik/docusaurus-theme/releases/node";
import { remarkLinkRewrite } from "@goauthentik/docusaurus-theme/remark";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const require = createRequire(import.meta.url);

const rootStaticDirectory = resolve(__dirname, "..", "static");
const packageStaticDirectory = resolve(__dirname, "static");
const authentikModulePath = resolve(__dirname, "..", "..");

const releaseEnvironment = prepareReleaseEnvironment();

//#region Copy static files

const brandFiles = new Map([
    [resolve(authentikModulePath, "lifecycle/container/compose.yml"), "compose.yml"],
    ["@goauthentik/brand-assets/icon.png", "img/icon.png"],
    ["@goauthentik/brand-assets/icon.svg", "img/icon.svg"],
    ["@goauthentik/brand-assets/social.png", "img/social.png"],
    // cspell:disable-next-line
    ["@goauthentik/brand-assets/icon_left_brand.svg", "img/icon_left_brand_colour.svg"],
    ["@goauthentik/brand-assets/icon_left_brand_white.svg", "img/icon_left_brand.svg"],
    // cspell:disable-next-line
    ["@goauthentik/brand-assets/icon_top_brand.svg", "img/icon_top_brand_colour.svg"],
    ["@goauthentik/brand-assets/icon_top_brand_white.svg", "img/icon_top_brand.svg"],
]);

await Promise.all(
    Array.from(brandFiles.entries(), async ([src, dest]) => {
        const srcPath = require.resolve(src);
        const destPath = resolve(rootStaticDirectory, dest);
        return cp(srcPath, destPath, { recursive: true });
    }),
);

const redirectPlugins = await createRedirectPlugins(resolve(packageStaticDirectory, "_redirects"));

//#endregion

/**
 * Generate Sidebar structure for CVEs. Items are grouped by year and sorted newest to old.
 *
 * @param {SidebarItemsGeneratorArgs} args
 * @returns {NormalizedSidebar}
 */
export function generateCVESidebar(args) {
    /** @type {{ [key: string]: NormalizedSidebarItemCategory}} */
    const yearCategories = {};
    args.docs
        .filter((item) => item.sourceDirName === "security/cves")
        .forEach((item) => {
            const matches = item.title.match(/CVE-(\d+)-/);
            if (!matches) {
                console.warn(`Could not extract year from CVE title: ${item.title}`);
                return;
            }
            const year = matches[1] || "";
            if (!Object.hasOwn(yearCategories, year)) {
                yearCategories[year] = {
                    type: "category",
                    label: year,
                    items: [],
                };
            }
            yearCategories[year]?.items.push({
                type: "doc",
                id: item.id,
            });
        });
    const categories = Object.values(yearCategories);
    categories.forEach((item) => {
        item.items.reverse();
    });
    categories.reverse();
    return categories;
}

//#region Configuration

export default createDocusaurusConfig(
    extendConfig({
        future: {
            faster: true,
        },
        clientModules: ["../docusaurus-theme/theme/utils/mermaid_icons.js"],
        url: DocusaurusURL.Docs,
        //#region Preset

        presets: [
            createClassicPreset({
                pages: false,
                docs: {
                    sidebarItemsGenerator: async ({ defaultSidebarItemsGenerator, ...args }) => {
                        const sidebarItems = await defaultSidebarItemsGenerator(args);
                        if (args.item.dirName === "security/cves") {
                            return generateCVESidebar(args);
                        }
                        return sidebarItems;
                    },
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
                            ["/integrations", DocusaurusURL.Integrations],
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

            createLLMSPlugin({
                sections: [{ path: ".", routeBasePath: "/" }],
                groupBy: "topic",
                // Normalized section headings for the top-level topics.
                categories: topics,
                // Split the glossary out of "Core Concepts" into its own section.
                regroup: [["core/glossary", "glossary"]],
                crossLinks: [
                    {
                        label: "Integrations",
                        url: new URL("llms.txt", DocusaurusURL.Integrations).toString(),
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
