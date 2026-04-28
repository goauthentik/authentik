/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import { createESLintPackageConfig, DefaultIgnorePatterns } from "@goauthentik/eslint-config";

import { defineConfig } from "eslint/config";

// @ts-check

/**
 * ESLint configuration for authentik's monorepo.
 * @type {Config[]}
 */
const eslintConfig = defineConfig(
    createESLintPackageConfig({
        parserOptions: {
            tsconfigRootDir: import.meta.dirname,
        },
        ignorePatterns: [
            // ---
            ...DefaultIgnorePatterns,
            "**/dist/**",
            "**/out/**",
            "**/vendored/**",
            "**/.wireit/**",
            "**/node_modules/",
            "**/.storybook/*",
            "coverage/",
            "src/locale-codes.ts",
            "playwright-report",
            "storybook-static/",
            "src/locales/",
            "**/*.min.js",
        ],
    }),
    {
        rules: {
            "no-console": "off",
        },
        files: ["packages/**/*"],
    },
    {
        rules: {
            "consistent-return": "off",
            "no-div-regex": "off",
            "no-empty-function": ["error", { allow: ["arrowFunctions"] }],
            "no-param-reassign": "off",
        },
    },
    {
        rules: {
            "vars-on-top": "off",
        },
        files: ["**/*.d.ts"],
    },
);

export default eslintConfig;
