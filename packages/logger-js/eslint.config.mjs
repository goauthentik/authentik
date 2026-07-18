/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import { createESLintPackageConfig } from "@goauthentik/eslint-config";

import { defineConfig } from "eslint/config";

// @ts-check

/**
 * @type {Config[]}
 */
const eslintConfig = defineConfig(
    createESLintPackageConfig({
        parserOptions: {
            tsconfigRootDir: import.meta.dirname,
        },
    }),
    {
        rules: {
            "no-console": "off",
        },
        files: ["shared/**"],
    },
);

export default eslintConfig;
