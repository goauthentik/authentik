import { createESLintPackageConfig } from "@goauthentik/eslint-config";

import { defineConfig } from "eslint/config";

// @ts-check

export default defineConfig(
    createESLintPackageConfig({
        parserOptions: {
            tsconfigRootDir: import.meta.dirname,
        },
    }),
);
