module.exports = {
    title: "authentik",
    tagline: "The authentication glue you need.",
    url: "https://goauthentik.io",
    baseUrl: "/",
    onBrokenLinks: "throw",
    favicon: "img/logo.png",
    organizationName: "BeryJu",
    projectName: "authentik",
    themeConfig: {
        navbar: {
            title: "authentik",
            logo: {
                alt: "authentik logo",
                src: "img/logo.svg",
            },
            hideOnScroll: true,
            items: [
                {
                    to: "docs/",
                    activeBasePath: "docs",
                    label: "Docs",
                    position: "left",
                },
                {
                    href: "https://github.com/beryju/authentik",
                    label: "GitHub",
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
                            href: "https://github.com/beryju/authentik",
                        },
                    ],
                },
            ],
            copyright: `Copyright © ${new Date().getFullYear()} BeryJu.org. Built with Docusaurus.`,
        },
        colorMode: {
            respectPrefersColorScheme: true,
        },
    },
    presets: [
        [
            "@docusaurus/preset-classic",
            {
                docs: {
                    sidebarPath: require.resolve("./sidebars.js"),
                    editUrl:
                        "https://github.com/beryju/authentik/edit/master/website/",
                },
                theme: {
                    customCss: require.resolve("./src/css/custom.css"),
                },
            },
        ],
    ],
};
