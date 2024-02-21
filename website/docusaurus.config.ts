const fs = require("fs").promises;
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

module.exports = async function (): Promise<Config> {
    const remarkGithub = (await import("remark-github")).default;
    const defaultBuildUrl = (await import("remark-github")).defaultBuildUrl;
    return {
        title: "authentik",
        tagline: "Bring all of your authentication into a unified platform.",
        url: "https://goauthentik.io",
        baseUrl: "/",
        onBrokenLinks: "throw",
        favicon: "img/icon.png",
        organizationName: "Authentik Security Inc.",
        projectName: "authentik",
        themeConfig: {
            image: "img/social.png",
            navbar: {
                logo: {
                    alt: "authentik logo",
                    src: "img/icon_left_brand.svg",
                },
                items: [
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
                additionalLanguages: ["python", "diff", "json"],
            },
        },
        presets: [
            [
                "@docusaurus/preset-classic",
                {
                    docs: {
                        id: "docs",
                        sidebarPath: require.resolve("./sidebars.js"),
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
                    blog: {
                        showReadingTime: true,
                        blogSidebarTitle: "All our posts",
                        blogSidebarCount: "ALL",
                    },
                } satisfies Preset.Options,
            ],
            [
                "redocusaurus",
                {
                    specs: [
                        {
                            id: "main",
                            spec: "static/schema.yaml",
                        },
                    ],
                },
            ],
        ],
        plugins: [
            [
                "@docusaurus/plugin-content-docs",
                {
                    id: "docsIntegrations",
                    path: "integrations",
                    routeBasePath: "integrations",
                    sidebarPath: require.resolve("./sidebarsIntegrations.js"),
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
                    sidebarPath: require.resolve("./sidebarsDev.js"),
                    editUrl:
                        "https://github.com/goauthentik/authentik/edit/main/website/",
                },
            ],
        ],
        markdown: {
            mermaid: true,
        },
        themes: ["@docusaurus/theme-mermaid"],
    };
};
