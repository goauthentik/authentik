/**
 * @file Docusaurus routing configuration.
 */

/**
 * @typedef {'production'|'development'} NodeEnvironment
 */

const NodeEnvironment = /** @type {NodeEnvironment} */ (process.env.NODE_ENV || "development");

/**
 * @satisfies {Record<NodeEnvironment, Record<string, string>>}
 */
export const DocusaurusURLByEnvironment = /** @type {const} */ ({
    development: {
        Docs: "http://localhost:3000",
        Integrations: "http://localhost:3001",
        WWW: "http://localhost:3002",
    },
    production: {
        Docs: "https://docs.goauthentik.io",
        Integrations: "https://integrations.goauthentik.io",
        WWW: "https://goauthentik.io",
    },
});

export const DocusaurusURL = DocusaurusURLByEnvironment[NodeEnvironment];

/**
 * @satisfies {Record<string, string>}
 */
export const SocialURL = /** @type {const} */ ({
    Discord: "https://goauthentik.io/discord",
    GitHub: "https://github.com/goauthentik/authentik",
});
