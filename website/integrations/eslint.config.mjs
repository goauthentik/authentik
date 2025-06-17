import { DefaultIgnorePatterns, createESLintPackageConfig } from "@goauthentik/eslint-config";

export default createESLintPackageConfig({
    ignorePatterns: [
        // ---
        ...DefaultIgnorePatterns,
        ".docusaurus/",
        "./build",
    ],
});
