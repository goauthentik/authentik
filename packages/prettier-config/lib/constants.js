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
 * @typedef {PrettierConfig & PackageJSONPluginConfig} ExtendedPrettierConfig
 */

const CI = !!process.env.CI;

/**
 * @type {ExtendedPrettierConfig['plugins']}
 */
const plugins = [
    // ---
    fileURLToPath(import.meta.resolve("@goauthentik/prettier-config/imports-plugin")),
];

/**
 * @type {ExtendedPrettierConfig['overrides']}
 */
const overrides = [
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
];

// Sort order can be a source of false-positives in CI when this package is updated.
if (!CI) {
    plugins.unshift("prettier-plugin-packagejson");
    overrides.push({
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
                "contributors",
                "funding",
                "repository",
                "bugs",
                "homepage",
                "scripts",
                "main",
                "type",
                "types",
                "exports",
                "imports",
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
                "workspaces",
                "files",
                "wireit",
                "resolutions",
                "engines",
                "devEngines",
                "packageManager",
                "prettier",
                "eslintConfig",
            ],
        },
    });
}

/**
 * authentik Prettier configuration.
 *
 * @type {ExtendedPrettierConfig}
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
    plugins,
    overrides,
};
