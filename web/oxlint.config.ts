/**
 * @file Oxlint configuration
 */

const { default: createOxlintConfig } = await import("@goauthentik/oxlint-config-dev").catch(() => {
    console.debug("Fallback to published @goauthentik/oxlint-config");
    // @ts-expect-error - Remove ignore after package is published.
    return import("@goauthentik/oxlint-config");
});

export default createOxlintConfig({ lit: true, react: true });
