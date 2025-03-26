import eslint from "@eslint/js";
import { reactConfig } from "@goauthentik/eslint-config/react-config";
import { typescriptConfig } from "@goauthentik/eslint-config/typescript-config";
import litconf from "eslint-plugin-lit";
import wcconf from "eslint-plugin-wc";
import tseslint from "typescript-eslint";

// @ts-check

/**
 * @typedef ESLintPackageConfigOptions Options for creating package ESLint configuration.
 * @property {string[]} [ignorePatterns] Override ignore patterns for ESLint.
 * @property {import("typescript-eslint").ConfigWithExtends} [overrides] Additional ESLint rules
 */

/**
 * @type {string[]} Default Ignore patterns for ESLint.
 */
export const DefaultIgnorePatterns = [
    // ---
    "**/*.md",
    "**/.yarn",
    "**/out",
    "**/dist",
];

/**
 * Given a preferred package name, creates a ESLint configuration object.
 *
 * @param {ESLintPackageConfigOptions} options The preferred package configuration options.
 *
 * @returns The ESLint configuration object.
 */
export function createESLintPackageConfig({
    ignorePatterns = DefaultIgnorePatterns,
    overrides = {},
} = {}) {
    return tseslint.config(
        {
            ignores: ignorePatterns,
        },

        eslint.configs.recommended,
        ...tseslint.configs.recommended,
        eslint.configs.recommended,
        wcconf.configs["flat/recommended"],
        litconf.configs["flat/recommended"],

        ...reactConfig,
        ...typescriptConfig,

        overrides,
    );
}
