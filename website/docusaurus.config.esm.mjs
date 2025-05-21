/**
 * @file Docusaurus config.
 *
 * @import * as Preset from "@docusaurus/preset-classic";
 * @import * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
 * @import { BuildUrlValues } from "remark-github";
 */
import { MonoRepoRoot } from "@goauthentik/core/paths/node";
import { createDocusaurusConfig } from "@goauthentik/docusaurus-config";
import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import remarkDirective from "remark-directive";
import remarkGithub, { defaultBuildUrl } from "remark-github";

import remarkEnterpriseDirective from "./remark/enterprise-directive.mjs";
import remarkPreviewDirective from "./remark/preview-directive.mjs";
import remarkSupportDirective from "./remark/support-directive.mjs";
import remarkVersionDirective from "./remark/version-directive.mjs";

const require = createRequire(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));
const staticDirectory = resolve(__dirname, "static");

/**
 * @param {string} fileName
 */
function copyStaticFile(fileName) {
    const source = resolve(MonoRepoRoot, fileName);
    const destination = resolve(staticDirectory, fileName);

    return cp(source, destination).catch((error) => {
        const wrapper = new Error(`Failed to copy file "${source}" to "${destination}"`);

        wrapper.cause = error;

        throw wrapper;
    });
}

await Promise.all([
    // ---
    copyStaticFile("docker-compose.yml"),
    copyStaticFile("schema.yml"),
]);
/**
 * Documentation site configuration for Docusaurus.
 */
const config = createDocusaurusConfig({
    url: "https://docs.goauthentik.io",
    future: {
        experimental_faster: true,
    },
    themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],
    themeConfig: {
        image: "img/social.png",
        navbar: {
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
                href: "https://goauthentik.io/",
                target: "_self",
            },
            items: [
                {
                    to: "https://goauthentik.io/features",
                    label: "Features",
                    position: "left",
                    target: "_self",
                },
                {
                    to: "integrations/",
                    label: "Integrations",
                    position: "left",
                },
                {
                    to: "docs/",
                    label: "Documentation",
                    position: "left",
                },
                {
                    to: "https://goauthentik.io/pricing/",
                    label: "Pricing",
                    position: "left",
                    target: "_self",
                },
                {
                    to: "https://goauthentik.io/blog",
                    label: "Blog",
                    position: "left",
                    target: "_self",
                },
                {
                    "href": "https://github.com/goauthentik/authentik",
                    "data-icon": "github",
                    "aria-label": "GitHub",
                    "position": "right",
                },
                {
                    "href": "https://goauthentik.io/discord",
                    "data-icon": "discord",
                    "aria-label": "Discord",
                    "position": "right",
                },
            ],
        },
        footer: {
            links: [],
            copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
        },
        algolia: {
            appId: "36ROD0O0FV",
            apiKey: "727db511300ca9aec5425645bbbddfb5",
            indexName: "goauthentik",
        },
    },
    presets: [
        [
            "@docusaurus/preset-classic",
            /** @type {Preset.Options} */ ({
                docs: {
                    id: "docs",
                    sidebarPath: "./sidebars/docs.mjs",
                    showLastUpdateTime: false,
                    editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
                    docItemComponent: "@theme/ApiItem",

                    beforeDefaultRemarkPlugins: [
                        remarkDirective,
                        remarkVersionDirective,
                        remarkEnterpriseDirective,
                        remarkPreviewDirective,
                        remarkSupportDirective,
                    ],
                    remarkPlugins: [
                        [
                            remarkGithub,
                            {
                                repository: "goauthentik/authentik",
                                /**
                                 * @param {BuildUrlValues} values
                                 */
                                buildUrl: (values) => {
                                    // Only replace issues and PR links
                                    return values.type === "issue" || values.type === "mention"
                                        ? defaultBuildUrl(values)
                                        : false;
                                },
                            },
                        ],
                    ],
                },
                theme: {
                    customCss: require.resolve("@goauthentik/docusaurus-config/css/index.css"),
                },
            }),
        ],
    ],
    plugins: [
        [
            "@docusaurus/plugin-content-docs",
            {
                id: "docsIntegrations",
                path: "integrations",
                routeBasePath: "integrations",
                sidebarPath: "./sidebars/integrations.mjs",
                editUrl: "https://github.com/goauthentik/authentik/edit/main/website/",
            },
        ],
        [
            "docusaurus-plugin-openapi-docs",
            {
                id: "api",
                docsPluginId: "docs",
                config: /** @type {OpenApiPlugin.Options} */ ({
                    authentik: {
                        specPath: "static/schema.yml",
                        outputDir: "docs/developer-docs/api/reference/",
                        hideSendButton: true,
                        sidebarOptions: {
                            groupPathsBy: "tag",
                        },
                    },
                }),
            },
        ],
    ],
});

export default config;
