const config = require("./docusaurus.config");

module.exports = async function () {
    const remarkGithub = (await import("remark-github")).default;
    const mainConfig = await config();
    return {
        title: "authentik",
        tagline: "Making authentication simple.",
        url: "https://goauthentik.io",
        baseUrl: "/if/help/",
        onBrokenLinks: "throw",
        favicon: "img/icon.png",
        organizationName: "BeryJu",
        projectName: "authentik",
        themeConfig: {
            navbar: {
                logo: {
                    alt: "authentik logo",
                    src: "img/icon_left_brand.svg",
                },
                items: [
                    {
                        to: "docs/",
                        activeBasePath: "docs",
                        label: "Docs",
                        position: "left",
                    },
                    {
                        to: "integrations/",
                        activeBasePath: "integrations",
                        label: "Integrations",
                        position: "left",
                    },
                    {
                        to: "developer-docs/",
                        activeBasePath: "developer-docs",
                        label: "Developer Docs",
                        position: "left",
                    },
                    {
                        href: "https://github.com/goauthentik/authentik",
                        label: "GitHub",
                        position: "right",
                    },
                    {
                        href: "https://goauthentik.io/discord",
                        label: "Discord",
                        position: "right",
                    },
                ],
            },
            footer: {
                links: [],
                copyright: mainConfig.themeConfig.footer.copyright,
            },
            colorMode: mainConfig.themeConfig.colorMode,
            tableOfContents: mainConfig.themeConfig.tableOfContents,
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
                                    buildUrl: function (
                                        values,
                                        defaultBuildUrl,
                                    ) {
                                        return values.type === "issue"
                                            ? defaultBuildUrl(values)
                                            : false;
                                    },
                                },
                            ],
                        ],
                    },
                    pages: false,
                    theme: {
                        customCss: require.resolve("./src/css/custom.css"),
                    },
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
            [
                "@docusaurus/plugin-client-redirects",
                {
                    redirects: [
                        {
                            to: "/docs/",
                            from: ["/"],
                        },
                    ],
                },
            ],
        ],
    };
};
