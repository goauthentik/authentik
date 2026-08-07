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
