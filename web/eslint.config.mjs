import { createESLintPackageConfig } from "@goauthentik/eslint-config";
import tseslint from "typescript-eslint";

// @ts-check

/**
 * ESLint configuration for authentik's monorepo.
 */
const ESLintConfig = createESLintPackageConfig({
    ignorePatterns: [
        "**/dist/**",
        "**/out/**",
        "**/.wireit/**",
        "**/node_modules/",
        "**/.storybook/*",
        "coverage/",
        "src/locale-codes.ts",
        "storybook-static/",
        "src/locales/",
    ],
});

export default tseslint.config(
    ...ESLintConfig,
    {
        rules: {
            "no-console": "off",
        },
        files: ["packages/**/*"],
    },
    {
        rules: {
            "no-void": "off",
            "no-implicit-coercion": "off",
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
            // "no-var": "off",
            "prefer-arrow-callback": "off",
            "react/jsx-no-leaked-render": "off",
            "vars-on-top": "off",
        },
    },
);
