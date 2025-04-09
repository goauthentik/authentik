import eslint from "@eslint/js";
import { javaScriptConfig } from "@goauthentik/eslint-config/javascript-config";
import { reactConfig } from "@goauthentik/eslint-config/react-config";
import { typescriptConfig } from "@goauthentik/eslint-config/typescript-config";
import * as litconf from "eslint-plugin-lit";
import * as wcconf from "eslint-plugin-wc";
import tseslint from "typescript-eslint";

// @ts-check

/**
 * @typedef ESLintPackageConfigOptions Options for creating package ESLint configuration.
 * @property {string[]} [ignorePatterns] Override ignore patterns for ESLint.
 */

/**
 * @type {string[]} Default Ignore patterns for ESLint.
 */
export const DefaultIgnorePatterns = [
    // ---
    "**/*.md",
    "**/out",
    "**/dist",
    "**/.wireit",
    "website/build/**",
    "website/.docusaurus/**",
    "**/node_modules",
    "**/coverage",
    "**/storybook-static",
    "**/locale-codes.ts",
    "**/src/locales",
    "**/gen-ts-api",
];

/**
 * Given a preferred package name, creates a ESLint configuration object.
 *
 * @param {ESLintPackageConfigOptions} options The preferred package configuration options.
 *
 * @returns The ESLint configuration object.
 */
export function createESLintPackageConfig({ ignorePatterns = DefaultIgnorePatterns } = {}) {
    return tseslint.config(
        {
            ignores: ignorePatterns,
        },

        eslint.configs.recommended,
        javaScriptConfig,

        wcconf.configs["flat/recommended"],
        litconf.configs["flat/recommended"],

        ...tseslint.configs.recommended,

        ...typescriptConfig,

        ...reactConfig,

        {
            rules: {
                "no-console": "off",
            },
            files: [
                // ---
                "**/scripts/**/*",
                "**/test/**/*",
                "**/tests/**/*",
            ],
        },
    );
}
