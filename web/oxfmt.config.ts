/**
 * @file Oxfmt configuration
 */

const { default: createOxfmtConfig } = await import("@goauthentik/oxfmt-config-dev").catch(() => {
    console.debug("Fallback to published @goauthentik/oxfmt-config");

    return import("@goauthentik/oxfmt-config");
});

export default createOxfmtConfig({
    // Carried over from the former .prettierignore.
    ignorePatterns: [
        "node_modules",
        "coverage",
        "dist",
        "out",
        "storybook-static",
        ".storybook/css-import-maps*",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
        "**/LICENSE",
        "**/*.min.js",
        "**/*.min.css",
        // Generated, and import order matters.
        "src/locale-codes.ts",
        "src/locales/**",
    ],
});
