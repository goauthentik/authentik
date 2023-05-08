const sidebar = require("./sidebars.js");

const releases = sidebar.docs
    .filter((doc) => doc.link?.slug === "releases")[0]
    .items.filter((release) => typeof release === "string");

/** @type {import('@docusaurus/types').DocusaurusConfig} */
module.exports = {
    title: "authentik",
    tagline: "Making authentication simple.",
    url: "https://goauthentik.io",
    baseUrl: "/",
    onBrokenLinks: "throw",
    favicon: "img/icon.png",
    organizationName: "Authentik Security Inc.",
    projectName: "authentik",
    themeConfig: {
        navbar: {
            title: "authentik",
            logo: {
                alt: "authentik logo",
                src: "img/icon_left_brand.svg",
            },
            items: [
                { to: "blog", label: "Blog", position: "left" },
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
                    to: "pricing/",
                    label: "Pricing",
                    position: "left",
                },
                {
                    to: "jobs/",
                    label: "Jobs",
                    position: "left",
                },
                {
                    type: "dropdown",
                    label: `Version: ${releases[0].replace(
                        /releases\/\d+\/v/,
                        ""
                    )}`,
                    position: "right",
                    items: releases.map((release) => {
                        const version = release.replace(/releases\/\d+\/v/, "");
                        const subdomain = version.replace(".", "-");
                        const label = `Version: ${version}`;
                        return {
                            label: label,
                            href: `https://version-${subdomain}.goauthentik.io`,
                        };
                    }),
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
            links: [
                {
                    title: "Documentation",
                    items: [
                        {
                            label: "Documentation",
                            to: "docs/",
                        },
                        {
                            label: "Integrations",
                            to: "integrations/",
                        },
                        {
                            label: "Developer Documentation",
                            to: "developer-docs/",
                        },
                        {
                            label: "Installations",
                            to: "docs/installation/",
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
                            href: "https://goauthentik.io/discord",
                        },
                    ],
                },
            ],
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
                },
                theme: {
                    customCss: require.resolve("./src/css/custom.css"),
                },
                gtag: {
                    trackingID: "G-9MVR9WZFZH",
                    anonymizeIP: true,
                },
                blog: {
                    showReadingTime: true,
                    blogSidebarTitle: "All our posts",
                    blogSidebarCount: "ALL",
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
    ],
    markdown: {
        mermaid: true,
    },
    themes: ["@docusaurus/theme-mermaid"],
    scripts: [
        {
            src: "https://goauthentik.io/js/script.js",
            async: true,
            "data-domain": "goauthentik.io",
        },
        {
            src: "https://boards.greenhouse.io/embed/job_board/js?for=authentiksecurity",
        },
    ],
};
