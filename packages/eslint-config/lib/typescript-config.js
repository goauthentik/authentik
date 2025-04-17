// @ts-check
import tseslint from "typescript-eslint";

import NodeLintPlugin from "../plugins/node-lint.js";

/**
 * ESLint configuration for TypeScript authentik projects.
 */
export const typescriptConfig = tseslint.config({
    plugins: {
        "node-lint": NodeLintPlugin,
    },

    rules: {
        "@typescript-eslint/ban-ts-comment": "off",
        // "@typescript-eslint/ban-ts-comment": [
        //     "error",
        //     {
        //         "ts-expect-error": "allow-with-description",
        //         "ts-ignore": true,
        //         "ts-nocheck": "allow-with-description",
        //         "ts-check": false,
        //         "minimumDescriptionLength": 5,
        //     },
        // ],
        "@typescript-eslint/no-explicit-any": "warn",
        "no-unused-private-class-members": "warn",
        "no-use-before-define": "off",
        // "@typescript-eslint/no-use-before-define": "error",
        "no-invalid-this": "off",
        "no-unused-vars": "off",
        "@typescript-eslint/triple-slash-reference": [
            "warn",
            {
                path: "never",
                types: "always",
                lib: "always",
            },
        ],
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
});

export default typescriptConfig;
