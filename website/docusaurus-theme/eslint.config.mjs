import { createESLintPackageConfig, DefaultIgnorePatterns } from "@goauthentik/eslint-config";

export default createESLintPackageConfig({
    parserOptions: {
        tsconfigRootDir: import.meta.dirname,
    },
    ignorePatterns: [
        // ---
        ...DefaultIgnorePatterns,
        "**/.docusaurus/",
    ],
});
