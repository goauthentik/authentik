import { DefaultIgnorePatterns, createESLintPackageConfig } from "@goauthentik/eslint-config";

// @ts-check

/**
 * ESLint configuration for authentik's monorepo.
 */
const ESLintConfig = createESLintPackageConfig({
    ignorePatterns: [
        // ---
        ...DefaultIgnorePatterns,
        ".docusaurus/",
        "./build",
    ],
});

export default ESLintConfig;
