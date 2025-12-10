/**
 * @file ESLint Configuration Entry Point
 *
 * @import { Config } from "eslint/config";
 * @import { ParserOptions } from "@typescript-eslint/parser";
 */

import { javaScriptConfig } from "./lib/javascript-config.js";
import { reactConfig } from "./lib/react-config.js";
import { typescriptConfig } from "./lib/typescript-config.js";

import eslint from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import tseslint from "typescript-eslint";

// @ts-check

const litconf = await import("eslint-plugin-lit").catch(() => null);
const wcconf = await import("eslint-plugin-wc").catch(() => null);

/**
 * @typedef ESLintPackageConfigOptions Options for creating package ESLint configuration.
 * @property {string[]} [ignorePatterns] Override ignore patterns for ESLint.
 * @property {ParserOptions} [parserOptions] Override options for TypeScript ESLint's parser.
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
 * @returns {Config[]} The ESLint configuration object.
 */
export function createESLintPackageConfig({
    ignorePatterns = DefaultIgnorePatterns,
    parserOptions = {},
} = {}) {
    return defineConfig(
        globalIgnores(ignorePatterns),

        {
            languageOptions: {
                parserOptions,
            },
        },

        eslint.configs.recommended,
        javaScriptConfig,

        wcconf?.configs["flat/recommended"] ?? [{}],
        litconf?.configs["flat/recommended"] ?? [{}],

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
