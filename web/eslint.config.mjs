import eslint from "@eslint/js";
import tsparser from "@typescript-eslint/parser";
import litconf from "eslint-plugin-lit";
import wcconf from "eslint-plugin-wc";
import globals from "globals";
import tseslint from "typescript-eslint";

export default [
    // You would not believe how much this change has frustrated users: ["if an ignores key is used
    // without any other keys in the configuration object, then the patterns act as global
    // ignores"](https://eslint.org/docs/latest/use/configure/ignore)
    {
        ignores: [
            "dist/",
            // don't lint the cache
            ".wireit/",
            // let packages have their own configurations
            "packages/",
            // don't ever lint node_modules
            "node_modules/",
            ".storybook/*",
            // don't lint build output (make sure it's set to your correct build folder name)
            // don't lint nyc coverage output
            "coverage/",
            "src/locale-codes.ts",
            "storybook-static/",
            "src/locales/",
        ],
    },
    eslint.configs.recommended,
    wcconf.configs["flat/recommended"],
    litconf.configs["flat/recommended"],
    ...tseslint.configs.recommended,
    {
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: 12,
                sourceType: "module",
            },
        },
        files: ["src/**"],
        rules: {
            "lit/attribute-names": "off",
            // "lit/attribute-names": "error",
            "lit/no-private-properties": "error",
            // "lit/prefer-nothing": "warn",
            "lit/no-template-bind": "error",
            "no-unused-vars": "off",
            "no-console": ["error", { allow: ["debug", "warn", "error"] }],
            "@typescript-eslint/ban-ts-comment": "off",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
        },
    },
    {
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: 12,
                sourceType: "module",
            },
            globals: {
                ...globals.nodeBuiltin,
                ...globals.node,
            },
        },
        files: ["scripts/*.mjs", "*.ts", "*.mjs"],
        rules: {
            "no-unused-vars": "off",
            // We WANT our scripts to output to the console!
            "no-console": "off",
            "@typescript-eslint/ban-ts-comment": "off",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
        },
    },
];
