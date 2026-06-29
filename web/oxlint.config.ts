/**
 * @file Oxlint configuration
 */

const config = await import("@goauthentik/oxlint-config-dev")
    .catch(() => {
        console.debug("Fallback to published @goauthentik/oxlint-config");
        // @ts-expect-error - Remove ignore after package is published.
        return import("@goauthentik/oxlint-config");
    })
    .then((module) => module.default);

export default config;
