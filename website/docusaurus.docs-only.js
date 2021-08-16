const mainConfig = require("./docusaurus.config");

module.exports = {
    title: "authentik",
    tagline: "Making authentication simple.",
    url: "https://goauthentik.io",
    baseUrl: "/help/",
    onBrokenLinks: "throw",
    favicon: "img/icon.png",
    organizationName: "BeryJu",
    projectName: "authentik",
    themeConfig: {
        navbar: {
            title: "authentik",
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
                    href: "https://discord.gg/jg33eMhnj6",
                    label: "Discord",
                    position: "right",
                },
            ],
        },
        footer: mainConfig.themeConfig.footer,
        colorMode: mainConfig.themeConfig.colorMode,
    },
    presets: [
        [
            "@docusaurus/preset-classic",
            {
                docs: {
                    id: "docs",
                    sidebarPath: require.resolve("./sidebars.js"),
                    editUrl: "https://github.com/goauthentik/authentik/edit/master/website/",
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
            '@docusaurus/plugin-content-docs',
            {
                id: 'docsDevelopers',
                path: 'developer-docs',
                routeBasePath: 'developer-docs',
                sidebarPath: require.resolve('./sidebarsDev.js'),
                editUrl: "https://github.com/goauthentik/authentik/edit/master/website/",
            },
        ],
        [
            '@docusaurus/plugin-client-redirects',
            {
                redirects: [
                    {
                        to: '/docs/',
                        from: ['/'],
                    },
                ],
            },
        ],
    ],
};
