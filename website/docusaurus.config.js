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
    ssrTemplate: `<!DOCTYPE html>
<html <%~ it.htmlAttributes %>>
  <head>
    <meta charset="UTF-8">
    <meta name="go-import" content="goauthentik.io/api git https://github.com/goauthentik/client-go">
    <meta name="viewport" content="width=device-width, initial-scale=0.86, maximum-scale=3.0, minimum-scale=0.86">
    <meta name="generator" content="Docusaurus v<%= it.version %>">
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
    <div id="outside-docusaurus">
      <span>Custom markup</span>
    </div>
    <% it.scripts.forEach((script) => { %>
      <script src="<%= it.baseUrl %><%= script %>"></script>
    <% }); %>
    <%~ it.postBodyTags %>
  </body>
</html>`
};
