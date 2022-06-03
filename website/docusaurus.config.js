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
                    href: "https://goauthentik.io/discord",
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
                            href: "https://goauthentik.io/discord",
                        },
                        {
                            html: `<a href="https://www.netlify.com" target="_blank" rel="noreferrer noopener" aria-label="Deploys by Netlify">
                                    <img src="https://www.netlify.com/img/global/badges/netlify-color-accent.svg" alt="Deploys by Netlify" />
                                </a>`,
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
