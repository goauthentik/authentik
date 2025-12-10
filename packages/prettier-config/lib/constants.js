/**
 * @file Prettier configuration for authentik.
 *
 * @import { Config as PrettierConfig } from "prettier";
 */

import { fileURLToPath } from "node:url";

/**
 * @typedef {object} PackageJSONPluginConfig
 * @property {string[]} [packageSortOrder] Custom ordering array.
 */

/**
 * authentik Prettier configuration.
 *
 * @type {PrettierConfig & PackageJSONPluginConfig}
 * @internal
 */
export const AuthentikPrettierConfig = {
    arrowParens: "always",
    bracketSpacing: true,
    embeddedLanguageFormatting: "auto",
    htmlWhitespaceSensitivity: "css",
    insertPragma: false,
    jsxSingleQuote: false,
    printWidth: 100,
    proseWrap: "preserve",
    quoteProps: "consistent",
    requirePragma: false,
    semi: true,
    singleQuote: false,
    tabWidth: 4,
    trailingComma: "all",
    useTabs: false,
    vueIndentScriptAndStyle: false,
    plugins: [
        // ---
        "prettier-plugin-packagejson",
        fileURLToPath(import.meta.resolve("@goauthentik/prettier-config/imports-plugin")),
    ],

    overrides: [
        {
            files: "schemas/**/*.json",
            options: {
                tabWidth: 2,
            },
        },
        {
            files: "tsconfig.json",
            options: {
                trailingComma: "none",
            },
        },
        {
            files: "package.json",
            options: {
                packageSortOrder: [
                    // ---
                    "name",
                    "version",
                    "description",
                    "license",
                    "private",
                    "author",
                    "authors",
                    "scripts",
                    "main",
                    "type",
                    "exports",
                    "imports",
                    "dependencies",
                    "devDependencies",
                    "peerDependencies",
                    "optionalDependencies",
                    "wireit",
                    "resolutions",
                    "engines",
                ],
            },
        },
    ],
};
