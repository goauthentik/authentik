/**
 * @file lit-html and Web Component lint rules, sourced from `eslint-plugin-lit` and
 * `eslint-plugin-wc`.
 *
 * oxlint's JS-plugin host is ESLint v9-compatible, so it loads these ESLint plugins directly via
 * `jsPlugins` — authentik consumes them unmodified rather than re-implementing the rules. The
 * enabled set mirrors each plugin's `flat/recommended` config, which is the exact set the former
 * `@goauthentik/eslint-config` applied.
 */

import { fileURLToPath } from "node:url";

/** A `jsPlugins` entry aliasing an ESLint plugin so its rules resolve under a short namespace. */
export interface JsPluginAlias {
    name: string;
    specifier: string;
}

/**
 * Resolves a plugin to an absolute path.
 *
 * @remarks
 * oxlint resolves a bare `jsPlugins` specifier relative to the consuming `oxlint.config.ts`, not to
 * this package. Both plugins are dependencies of *this* package, so resolving them here means a
 * consumer never has to re-declare them, and resolution does not depend on the consumer's
 * `node_modules` layout.
 *
 * @param specifier The plugin's package name.
 *
 * @returns An absolute path to the plugin's entry point.
 */
function resolvePlugin(specifier: string): string {
    return fileURLToPath(import.meta.resolve(specifier));
}

/**
 * `jsPlugins` entries that load the ESLint web-component plugins. Aliased to `wc`/`lit` so the rule
 * names match each plugin's published rule namespace.
 */
export const WebComponentJsPlugins: JsPluginAlias[] = [
    { name: "wc", specifier: resolvePlugin("eslint-plugin-wc") },
    { name: "lit", specifier: resolvePlugin("eslint-plugin-lit") },
];

/**
 * The `flat/recommended` rules of `eslint-plugin-wc` and `eslint-plugin-lit`. These cover
 * web-component class pitfalls and lit-html template correctness that oxlint's built-in rules do not.
 */
export const WebComponentRules: Record<string, string> = {
    // eslint-plugin-wc — flat/recommended
    "wc/no-constructor-attributes": "error",
    "wc/no-invalid-element-name": "error",
    "wc/no-self-class": "error",

    // eslint-plugin-lit — flat/recommended
    "lit/attribute-value-entities": "error",
    "lit/binding-positions": "error",
    "lit/no-duplicate-template-bindings": "error",
    "lit/no-invalid-html": "error",
    "lit/no-legacy-template-syntax": "error",
    "lit/no-property-change-update": "error",
};
