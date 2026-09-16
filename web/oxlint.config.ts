/**
 * @file Oxlint configuration
 */

const { default: createOxlintConfig } = await import("@goauthentik/oxlint-config-dev").catch(() => {
    console.debug("Fallback to published @goauthentik/oxlint-config");

    return import("@goauthentik/oxlint-config");
});

export default createOxlintConfig({ lit: true, react: true });
