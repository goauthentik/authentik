import { createESLintPackageConfig } from "@goauthentik/eslint-config";

export default createESLintPackageConfig({
    parserOptions: {
        tsconfigRootDir: import.meta.dirname,
    },
});
