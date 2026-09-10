/**
 * @file lit-html and Web Component lint rules, sourced from `eslint-plugin-lit` and
 * `eslint-plugin-wc`.
 *
 * oxlint's JS-plugin host is ESLint v9-compatible, so it loads these ESLint plugins directly via
 * `jsPlugins` — authentik consumes them unmodified rather than re-implementing the rules. The
 * enabled set mirrors each plugin's `flat/recommended` config, which is the exact set the former
 * `@goauthentik/eslint-config` applied.
 */

/** A `jsPlugins` entry aliasing an ESLint plugin so its rules resolve under a short namespace. */
export interface JsPluginAlias {
    name: string;
    specifier: string;
}

/**
 * `jsPlugins` entries that load the ESLint web-component plugins. Aliased to `wc`/`lit` so the rule
 * names match each plugin's published rule namespace.
 */
export const WebComponentJsPlugins: JsPluginAlias[] = [
    { name: "wc", specifier: "eslint-plugin-wc" },
    { name: "lit", specifier: "eslint-plugin-lit" },
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
