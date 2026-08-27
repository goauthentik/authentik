/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import css from "@eslint/css";

// @ts-check

/**
 * @type {Config[]}
 */

export default [
    {
        ignores: [".wireit/**", "public/**", "**/*.{js,mjs,cjs,ts,mts,cts}"],
    },
    {
        files: ["dist/*.css"],
        plugins: {
            css,
        },
        language: "css/css",
        rules: {
            "css/no-duplicate-imports": "error",
        },
    },
];
