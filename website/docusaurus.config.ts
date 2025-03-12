import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import { themes as prismThemes } from "prism-react-renderer";
import type * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";
import remarkGithub, { BuildUrlValues } from "remark-github";
import { defaultBuildUrl } from "remark-github";
import remarkDirective from "remark-directive";
import remarkVersionDirective from "./remark/version-directive";
import remarkPreviewDirective from "./remark/preview-directive";
import remarkSupportDirective from "./remark/support-directive";

const createConfig = (): Config => {
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
                        label: "Documentation",
                        position: "left",
                    },
                    {
                        to: "integrations/",
                        label: "Integrations",
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
                additionalLanguages: [
                    // ---
                    "apacheconf",
                    "diff",
                    "http",
                    "json",
                    "nginx",
                    "python",
                    "bash",
                ],
            },
        },
        presets: [
            [
                "@docusaurus/preset-classic",
                {
                    docs: {
                        id: "docs",
                        sidebarPath: "./sidebars.js",
                        showLastUpdateTime:
                            process.env.GIT_UNAVAILABLE != "true",
                        editUrl:
                            "https://github.com/goauthentik/authentik/edit/main/website/",
                        docItemComponent: "@theme/ApiItem",
                        beforeDefaultRemarkPlugins: [
                            remarkDirective,
                            remarkVersionDirective,
                            remarkPreviewDirective,
                            remarkSupportDirective,
                        ],
                        remarkPlugins: [
                            [
                                remarkGithub,
                                {
                                    repository: "goauthentik/authentik",
                                    // Only replace issues and PR links
                                    buildUrl: (values: BuildUrlValues) => {
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
                "docusaurus-plugin-openapi-docs",
                {
                    id: "api",
                    docsPluginId: "docs",
                    config: {
                        authentik: {
                            specPath: "static/schema.yml",
                            outputDir: "docs/developer-docs/api/reference/",
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
        future: {
            experimental_faster: true,
        },
        themes: ["@docusaurus/theme-mermaid", "docusaurus-theme-openapi-docs"],
    };
};

module.exports = createConfig;
