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
            "no-void": "off",
            "@typescript-eslint/ban-ts-comment": "off",
            "@typescript-eslint/no-unused-vars": "off",
            "@typescript-eslint/no-use-before-define": "off",
            "array-callback-return": "off",
            "block-scoped-var": "off",
            "consistent-return": "off",
            "func-names": "off",
            "guard-for-in": "off",
            "no-div-regex": "off",
            "no-empty-function": "off",
            "no-param-reassign": "off",
            // "no-var": "off",
            "prefer-arrow-callback": "off",
            "react/jsx-no-leaked-render": "off",
            "vars-on-top": "off",
        },
    },
);

export default eslintConfig;
