/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

// @ts-check

/**
 * @type {Config[]}
 */
const eslintConfig = defineConfig(
    // Global ignores. Compiled output does not need to be linted, and `.wireit` is a cache.
    { ignores: ["dist/**", "public/**", ".wireit/**"] },
    {
        extends: [js.configs.recommended, tseslint.configs.recommended],
        rules: {
            "@typescript-eslint/ban-ts-comment": [
                "error",
                {
                    "ts-expect-error": "allow-with-description",
                    "ts-ignore": true,
                    "ts-nocheck": "allow-with-description",
                    "ts-check": false,
                    "minimumDescriptionLength": 5,
                },
            ],
            "no-use-before-define": "off",
            "@typescript-eslint/no-use-before-define": "error",
            "no-invalid-this": "off",
            "no-unused-vars": "off",
            "@typescript-eslint/no-namespace": "off",
            "@typescript-eslint/no-unused-vars": [
                "warn",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
        },
    },

    // The demo page is plain browser JavaScript.
    {
        files: ["demo/**/*.js"],
        languageOptions: {
            globals: {
                console: "readonly",
                document: "readonly",
                fetch: "readonly",
                getComputedStyle: "readonly",
                matchMedia: "readonly",
            },
        },
    },

    // Scripts run under Node, where `console` is legal.
    {
        files: ["*.mjs"],
        languageOptions: {
            globals: {
                console: "readonly",
            },
        },
    },
);

export default eslintConfig;
