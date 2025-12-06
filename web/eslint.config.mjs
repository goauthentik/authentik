/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import { createESLintPackageConfig, DefaultIgnorePatterns } from "@goauthentik/eslint-config";

import { defineConfig } from "eslint/config";

// @ts-check

/**
 * @typedef RestrictedImportEntry An entry describing a restricted import and it's remedy.
 * @property name {string} The restricted import name.
 * @property message {string} The message to show when the import is restricted.
 */

/**
 * @typedef RestrictedImportPattern An entry describing a restricted import pattern and it's remedy.
 * @property regex {string} The restricted import pattern regex.
 * @property message {string} The message to show when the import is restricted.
 */

/**
 * @typedef RestrictedImportsOptions An entry describing a restricted import rule.
 * @property patterns {RestrictedImportPattern[]} The restricted import patterns.
 * @property [paths] {RestrictedImportEntry[]} Optional restricted import paths.
 */

const submodules = new Set(
    /** @type {const} */ ([
        "styles",
        "common",
        "elements",
        "components",
        "admin",
        "user",
        "flow",
        "rac",
    ]),
);

/**
 * @typedef {(typeof submodules) extends Set<infer U> ? U : never} SubModule
 */

/**
 *
 * @param {SubModule} subpath
 * @param {Iterable<SubModule>} allowed
 * @returns {Config}
 */
function defineImportRestrictions(subpath, allowed) {
    const allowedSet = new Set(allowed);
    const restricted = submodules
        // ---
        .difference(allowedSet)
        .add(subpath);

    /**
     * @type {RestrictedImportsOptions}
     */
    const options = {
        patterns: Array.from(restricted, (mod) => ({
            regex: `#${mod}/.+`,
            message: `Cross-submodule import from #${mod} to #${subpath} is restricted. Consider moving the imported file to a #common if shared usage is intended.`,
        })),
    };

    return {
        rules: {
            "no-restricted-imports": ["warn", options],
        },
        files: Array.from(allowedSet, (mod) => `src/${mod}/**/*`),
    };
}

/**
 * @type {Map<SubModule, SubModule[]>}
 */
const submoduleOrganization = new Map([
    ["common", ["styles"]],
    ["elements", ["styles", "common"]],
    ["admin", ["styles", "common", "elements", "components"]],
    ["user", ["styles", "common", "elements", "components"]],
]);

/**
 * ESLint configuration for authentik's monorepo.
 * @type {Config[]}
 */
const eslintConfig = defineConfig(
    createESLintPackageConfig({
        parserOptions: {
            tsconfigRootDir: import.meta.dirname,
        },
        ignorePatterns: [
            // ---
            ...DefaultIgnorePatterns,
            "**/dist/**",
            "**/out/**",
            "**/vendored/**",
            "**/.wireit/**",
            "**/node_modules/",
            "**/.storybook/*",
            "coverage/",
            "src/locale-codes.ts",
            "playwright-report",
            "storybook-static/",
            "src/locales/",
            "**/*.min.js",
        ],
    }),
    {
        rules: {
            "no-console": "off",
        },
        files: ["packages/**/*"],
    },
    {
        rules: {
            "consistent-return": "off",
            "no-div-regex": "off",
            "no-empty-function": ["error", { allow: ["arrowFunctions"] }],
            "no-param-reassign": "off",
        },
    },
    ...Array.from(submoduleOrganization, ([target, allowed]) => {
        return defineImportRestrictions(target, allowed);
    }),
    {
        rules: {
            "vars-on-top": "off",
        },
        files: ["**/*.d.ts"],
    },
);

export default eslintConfig;
