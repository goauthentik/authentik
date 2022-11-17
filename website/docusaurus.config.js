const sidebar = require("./sidebars.js");

const releases = sidebar.docs
    .filter((doc) => doc.link?.slug === "releases")[0]
    .items.filter((release) => typeof release === "string");

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
                { to: "blog", label: "Blog", position: "left" },
                {
                    to: "docs/",
                    activeBasePath: "docs",
                    label: "Documentation",
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
                    label: "Developer",
                    position: "left",
                },
                {
                    to: "jobs/",
                    activeBasePath: "jobs",
                    label: "Jobs",
                    position: "left",
                },
                {
                    type: "dropdown",
                    label: `Version: latest`,
                    position: "right",
                    items: releases.map((release) => {
                        const subdomain = release
                            .replace("releases/v", "")
                            .replace(".", "-");
                        const label =
                            "Version: " + release.replace("releases/", "");
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
                            href: "https://goauthentik.io/discord",
                        },
                    ],
                },
            ],
            copyright: `Copyright © ${new Date().getFullYear()} authentik Security Inc. Built with Docusaurus.`,
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
    ssrTemplate: `<!DOCTYPE html>
<html <%~ it.htmlAttributes %>>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=0.86, maximum-scale=3.0, minimum-scale=0.86">
    <meta name="generator" content="Docusaurus v<%= it.version %>">
    <script async defer data-domain="goauthentik.io" src="https://goauthentik.io/js/script.js"></script>
    <%~ it.headTags %>
    <% it.metaAttributes.forEach((metaAttribute) => { %>
      <%~ metaAttribute %>
    <% }); %>
    <% it.stylesheets.forEach((stylesheet) => { %>
      <link rel="stylesheet" href="<%= it.baseUrl %><%= stylesheet %>" />
    <% }); %>
    <% it.scripts.forEach((script) => { %>
      <link rel="preload" href="<%= it.baseUrl %><%= script %>" as="script">
    <% }); %>
  </head>
  <body <%~ it.bodyAttributes %> itemscope="" itemtype="http://schema.org/Organization">
    <%~ it.preBodyTags %>
    <div id="__docusaurus">
      <%~ it.appHtml %>
    </div>
    <% it.scripts.forEach((script) => { %>
      <script src="<%= it.baseUrl %><%= script %>"></script>
    <% }); %>
    <%~ it.postBodyTags %>
  </body>
</html>`,
};
