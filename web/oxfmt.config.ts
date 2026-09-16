/**
 * @file Oxfmt configuration
 */

const config = await import("@goauthentik/oxfmt-config-dev")
    .catch(() => {
        console.debug("Fallback to published @goauthentik/oxfmt-config");

        return import("@goauthentik/oxfmt-config");
    })
    .then((module) => module.default);

export default config;
