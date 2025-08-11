import { createESLintPackageConfig, DefaultIgnorePatterns } from "@goauthentik/eslint-config";

export default createESLintPackageConfig({
    ignorePatterns: [
        // ---
        ...DefaultIgnorePatterns,
        "**/.docusaurus/",
        "**/build",
        "**/reference",
    ],
});
