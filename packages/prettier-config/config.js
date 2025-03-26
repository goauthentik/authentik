/**
 * authentik Prettier configuration.
 *
 * @type {import("prettier").Config}
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
    plugins: ["prettier-plugin-packagejson", "@trivago/prettier-plugin-sort-imports"],
    importOrder: ["^(@?)lit(.*)$", "\\.css$", "^@goauthentik/api$", "^[./]"],
    importOrderSeparation: true,
    importOrderSortSpecifiers: true,
    importOrderParserPlugins: ["typescript", "jsx", "classProperties", "decorators-legacy"],
    overrides: [
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
                    "scripts",
                    "devDependencies",
                    "dependencies",
                ],
            },
        },
    ],
};
