/**
 * @file Prettier config resolver.
 *
 * This file attempts to import the monorepo's local Prettier config package,
 * falling back to the published version if the local one cannot be found.
 */

const config = await import("@goauthentik/prettier-config-dev")
    .catch(() => {
        console.debug("Fallback to published @goauthentik/prettier-config");
        return import("@goauthentik/prettier-config");
    })
    .then((module) => module.default);

export default config;
