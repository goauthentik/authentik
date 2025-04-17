/**
 * @file Prettier configuration for authentik.
 *
 * @import { Config as PrettierConfig } from "prettier";
 * @import { PluginConfig as SortPluginConfig } from "@trivago/prettier-plugin-sort-imports";
 *
 * @typedef {object} PackageJSONPluginConfig
 * @property {string[]} [packageSortOrder] Custom ordering array.
 */

/**
 * authentik Prettier configuration.
 *
 * @type {PrettierConfig & SortPluginConfig & PackageJSONPluginConfig}
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
    quoteProps: "as-needed",
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
        "@trivago/prettier-plugin-sort-imports",
        "prettier-plugin-django-alpine",
    ],
    importOrder: [
        // ---
        // Lit Imports
        "^(@?)lit(.*)$",
        // CSS Imports
        "\\.css$",
        // API Imports
        "^@goauthentik/api$",
        // Relative Imports
        "^[./]",
    ],
    importOrderSeparation: true,
    importOrderSortSpecifiers: true,
    importOrderParserPlugins: ["typescript", "jsx", "classProperties", "decorators-legacy"],
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
            files: "authentik/**/*.html",
            options: {
                tabWidth: 2,
                parser: "html",
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
