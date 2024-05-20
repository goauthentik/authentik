import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import { themes as prismThemes } from "prism-react-renderer";
import type * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";

module.exports = async function (): Promise<Config> {
    const remarkGithub = (await import("remark-github")).default;
    const defaultBuildUrl = (await import("remark-github")).defaultBuildUrl;
    return {
        title: "authentik",
        tagline: "Bring all of your authentication into a unified platform.",
        url: "https://docs.goauthentik.io",
        baseUrl: "/",
        onBrokenLinks: "throw",
        onBrokenAnchors: "throw",
        favicon: "img/icon.png",
        organizationName: "Authentik Security Inc.",
        projectName: "authentik",
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
                        to: "https://goauthentik.io/blog",
                        label: "Blog",
                        position: "left",
                        target: "_self",
                    },
                    {
                        to: "docs/",
                        label: "Docs",
                        position: "left",
                    },
                    {
                        to: "integrations/",
                        label: "Integrations",
                        position: "left",
                    },
                    {
                        to: "developer-docs/",
                        label: "Developer",
                        position: "left",
                    },
                    {
                        to: "https://goauthentik.io/pricing/",
                        label: "Pricing",
                        position: "left",
                        target: "_self",
                    },
                    {
                        href: "https://github.com/goauthentik/authentik",
                        className: "header-github-link",
                        "aria-label": "GitHub repository",
                        position: "right",
                    },
                    {
                        href: "https://goauthentik.io/discord",
                        className: "header-discord-link",
                        "aria-label": "GitHub repository",
                        position: "right",
                    },
                ],
            },
            footer: {
                links: [],
                copyright: `Copyright © ${new Date().getFullYear()} Authentik Security Inc. Built with Docusaurus.`,
            },
            tableOfContents: {
                maxHeadingLevel: 5,
            },
            colorMode: {
                respectPrefersColorScheme: true,
            },
            algolia: {
                appId: "36ROD0O0FV",
                apiKey: "727db511300ca9aec5425645bbbddfb5",
                indexName: "goauthentik",
            },
            prism: {
                theme: prismThemes.oneLight,
                darkTheme: prismThemes.oneDark,
                additionalLanguages: ["python", "diff", "json"],
            },
        },
        presets: [
            [
                "@docusaurus/preset-classic",
                {
                    docs: {
                        id: "docs",
                        sidebarPath: "./sidebars.js",
                        editUrl:
                            "https://github.com/goauthentik/authentik/edit/main/website/",
                        remarkPlugins: [
                            [
                                remarkGithub,
                                {
                                    repository: "goauthentik/authentik",
                                    // Only replace issues and PR links
                                    buildUrl: function (values) {
                                        return values.type === "issue" ||
                                            values.type === "mention"
                                            ? defaultBuildUrl(values)
                                            : false;
                                    },
                                },
                            ],
                        ],
                    },
                    theme: {
                        customCss: require.resolve("./src/css/custom.css"),
                    },
                } satisfies Preset.Options,
            ],
        ],
        plugins: [
            [
                "@docusaurus/plugin-content-docs",
                {
                    id: "docsIntegrations",
                    path: "integrations",
                    routeBasePath: "integrations",
                    sidebarPath: "./sidebarsIntegrations.js",
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/",
                },
            ],
            [
                "@docusaurus/plugin-content-docs",
                {
                    id: "docsDevelopers",
                    path: "developer-docs",
                    routeBasePath: "developer-docs",
                    sidebarPath: "./sidebarsDev.js",
                    docItemComponent: "@theme/ApiItem",
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/",
                },
            ],
            [
                "docusaurus-plugin-openapi-docs",
                {
                    id: "api",
                    docsPluginId: "docsDevelopers",
                    config: {
                        authentik: {
                            specPath: "static/schema.yaml",
                            outputDir: "developer-docs/api/reference/",
                            hideSendButton: true,
                            sidebarOptions: {
                                groupPathsBy: "tag",
                            },
                        } satisfies OpenApiPlugin.Options,
                    },
                },
            ],
        ],
        markdown: {
            mermaid: true,
        },
        themes: ["docusaurus-theme-openapi-docs"],
    };
};
