module.exports = {
    title: "authentik",
    tagline: "Making authentication simple.",
    url: "https://goauthentik.io",
    baseUrl: "/",
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
                    to: "api/",
                    activeBasePath: "api",
                    label: "API",
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
        footer: {
            links: [
                {
                    title: "Docs",
                    items: [
                        {
                            label: "Documentation",
                            to: "docs/",
                        },
                        {
                            label: "Developer Documentation",
                            to: "developer-docs/",
                        },
                        {
                            label: "Installations",
                            to: "docs/installation/index",
                        },
                    ],
                },
                {
                    title: "More",
                    items: [
                        {
                            label: "GitHub",
                            href: "https://github.com/goauthentik/authentik",
                        },
                        {
                            label: "Discord",
                            href: "https://discord.gg/jg33eMhnj6",
                        },
                    ],
                },
            ],
            copyright: `Copyright © ${new Date().getFullYear()} BeryJu.org. Built with Docusaurus.`,
        },
        colorMode: {
            respectPrefersColorScheme: true,
        },
        algolia: {
            apiKey: '1b60b8f630b127697cbe0d3b31841470',
            indexName: 'goauthentik',
        },
    },
    clientModules: [
        require.resolve('./src/sentry.jsx'),
    ],
    presets: [
        [
            "@docusaurus/preset-classic",
            {
                docs: {
                    id: "docs",
                    sidebarPath: require.resolve("./sidebars.js"),
                    editUrl: "https://github.com/goauthentik/authentik/edit/master/website/",
                },
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
    ],
};
