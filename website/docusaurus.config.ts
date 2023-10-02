const fs = require("fs").promises;
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
const generateNavbarDropdown = require("./src/utils.js").generateNavbarDropdown;

module.exports = async function (): Promise<Config> {
    const remarkGithub = (await import("remark-github")).default;
    const defaultBuildUrl = (await import("remark-github")).defaultBuildUrl;
    return {
        title: "authentik",
        tagline: "Bring all of your authentication into a unified platform.",
        url: "https://docs.goauthentik.io",
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
                    src: "img/icon.svg",
                    href: "https://goauthentik.io/",
                    target: "_self",
                },
                items: [
                    { to: "blog", label: "Why authentik", position: "left" },
                    {
                        type: "html",
                        className:
                            "dropdown dropdown--hoverable dropdown--custom",
                        value: generateNavbarDropdown(
                            "Platform",
                            [
                                {
                                    label: "Get started",
                                    items: [
                                        {
                                            label: "Docker compose",
                                            to: "docs/installation/docker-compose",
                                        },
                                        {
                                            label: "Kubernetes",
                                            to: "docs/installation/kubernetes",
                                        },
                                    ],
                                },
                                {
                                    label: "Documentation",
                                    items: [
                                        {
                                            label: "Installation",
                                            to: "docs/installation/",
                                        },
                                        {
                                            label: "Integrations",
                                            to: "integrations/",
                                        },
                                        {
                                            label: "Release notes",
                                            to: "docs/releases/",
                                        },
                                        {
                                            label: "Roadmap",
                                            to: "docs/",
                                        },
                                    ],
                                },
                                {
                                    label: "Solutions",
                                    items: [
                                        {
                                            label: "Work",
                                            to: "docs/installation/",
                                        },
                                        {
                                            label: "foo",
                                            to: "docs/",
                                        },
                                        {
                                            label: "bar",
                                            to: "integrations/",
                                        },
                                        {
                                            label: "baz",
                                            to: "integrations/",
                                        },
                                    ],
                                },
                            ],
                            `<div class="category enterprise">
                                <p>Enterprise</p>
                                <ul>
                                    <li><a class="dropdown__link" href="">Advantages</a></li>
                                    <li><a class="dropdown__link" href="">Support</a></li>
                                    <li><a class="dropdown__link" href="">Pricing</a></li>
                                </ul>
                            </div>`,
                        ),
                        position: "left",
                    },
                    {
                        label: "Integrations",
                        to: "integrations/",
                    },
                    {
                        label: "Pricing",
                        to: "pricing/",
                    },
                    {
                        type: "html",
                        className:
                            "dropdown dropdown--hoverable dropdown--custom",
                        value: generateNavbarDropdown("Community", [
                            {
                                label: "Connect",
                                items: [
                                    {
                                        label: "Blog",
                                        to: "blog/",
                                    },
                                    {
                                        label: "Discord",
                                        to: "https://goauthentik.io/discord",
                                    },
                                    {
                                        label: "GitHub",
                                        to: "https://github.com/goauthentik/authentik",
                                    },
                                ],
                            },
                            {
                                label: "Developer",
                                items: [
                                    {
                                        label: "Set up authentik",
                                        to: "developer-docs/setup/full-dev-environment/",
                                    },
                                    {
                                        label: "Writing documentation",
                                        to: "developer-docs/docs/writing-documentation",
                                    },
                                ],
                            },
                            {
                                label: "Community",
                                items: [
                                    {
                                        label: "Contributing",
                                        to: "developer-docs/",
                                    },
                                    {
                                        label: "Events",
                                        to: "developer-docs/events",
                                    },
                                ],
                            },
                            {
                                label: "Resources",
                                items: [
                                    {
                                        label: "Icons & Branding",
                                        to: "developer-docs/",
                                    },
                                ],
                            },
                        ]),
                        position: "left",
                    },
                    {
                        type: "html",
                        className:
                            "dropdown dropdown--hoverable dropdown--custom",
                        value: generateNavbarDropdown("About us", [
                            {
                                label: "",
                                items: [
                                    {
                                        label: "The company",
                                        to: "",
                                    },
                                    {
                                        label: "Jobs",
                                        to: "",
                                    },
                                    {
                                        label: "Team",
                                        to: "",
                                    },
                                    {
                                        label: "Contact us",
                                        to: "",
                                    },
                                ],
                            },
                        ]),
                        position: "left",
                        target: "_self",
                    },
                    {
                        href: "https://github.com/goauthentik/authentik",
                        className: "header-github-link",
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
