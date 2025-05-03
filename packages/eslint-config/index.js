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
    "**/.venv",
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
                "**/esbuild-plugin-live-reload/**/*",
                "**/test/**/*",
                "**/tests/**/*",
            ],
        },

        //#region TODO Incomplete Rules
        {
            // The following rules are disabled because the changes needed to satisfy them are
            // are large enough to warrant several follow-up PRs.
            rules: {
                // TODO: High priority, common and easy to fix.
                "eqeqeq": "off",
                // TODO: High priority, common and easy to fix.
                "no-sparse-arrays": "off",
                // TODO: High priority, common and easy to fix.
                "no-lonely-if": "off",
                // TODO: Reconsider this rule.
                "dot-notation": "off",
                // TODO: Reconsider this rule.
                "no-implicit-coercion": "off",
                // TODO: Reconsider this rule.
                "prefer-template": "off",
                "@typescript-eslint/ban-ts-comment": "off",
                "@typescript-eslint/no-unused-vars": "off",
                "@typescript-eslint/no-use-before-define": "off",
                "array-callback-return": "off",
                "block-scoped-var": "off",
                "consistent-return": "off",
                "func-names": "off",
                "guard-for-in": "off",
                "no-bitwise": "off",
                "no-div-regex": "off",
                "no-else-return": "off",
                "no-empty-function": "off",
                "no-param-reassign": "off",
                "no-throw-literal": "off",
                "no-var": "off",
                "prefer-arrow-callback": "off",
                "react/jsx-no-leaked-render": "off",
                "vars-on-top": "off",
            },
        },

        //#endregion
    );
}
