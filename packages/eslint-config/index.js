import eslint from "@eslint/js";
import * as litconf from "eslint-plugin-lit";
import * as wcconf from "eslint-plugin-wc";
import tseslint from "typescript-eslint";

import { javaScriptConfig } from "./lib/javascript-config.js";
import { reactConfig } from "./lib/react-config.js";
import { typescriptConfig } from "./lib/typescript-config.js";

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
    // TODO: Replace after moving to `docs` directory.
    "website/**/build/**",
    "website/**/.docusaurus/**",
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
