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
        "@trivago/prettier-plugin-sort-imports",
    ],
    importOrder: [
        // ---

        "^(@goauthentik/|#)common.+",
        "^(@goauthentik/|#)elements.+",
        "^(@goauthentik/|#)components.+",
        "^(@goauthentik/|#)user.+",
        "^(@goauthentik/|#)admin.+",
        "^(@goauthentik/|#)flow.+",
        "^(@goauthentik/|#)flow.+",

        "^#.+",
        "^@goauthentik.+",

        "<THIRD_PARTY_MODULES>",

        "^(@?)lit(.*)$",
        "\\.css$",
        "^@goauthentik/api$",
        "^[./]",
    ],
    importOrderSideEffects: false,
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
