import { PaddingRules } from "./padding-rules.js";
import { createRuntimeOverrides } from "./restrictions.js";
import { WebComponentJsPlugins, WebComponentRules } from "./web-components.js";

import type { DummyRuleMap, ExternalPluginEntry, OxlintConfig } from "oxlint";

export * from "./padding-rules.js";
export * from "./restrictions.js";
export * from "./web-components.js";

export interface OxlintConfigOptions {
    /** The package namespace whose runtime boundaries are enforced, e.g. `@goauthentik`. */
    packageNamespace?: string;
    /** Enable oxlint's React plugin (off by default). */
    react?: boolean;
    /**
     * Enable the lit-html and Web Component lint rules (`eslint-plugin-lit` + `eslint-plugin-wc`,
     * loaded as `jsPlugins`). Off by default; the web UI turns it on.
     */
    lit?: boolean;
    /**
     * Enable the blank-line padding rules (`padding-lines`, `console-padding`,
     * `multiline-statement-padding`). Off by default.
     *
     * @remarks
     *   These autofix by rewriting source, so switching them on reformats a codebase that has not
     *   been written to them. Opt in deliberately, and land the resulting fix in its own commit.
     */
    padding?: boolean;
    /** Override the default ignore patterns. */
    ignorePatterns?: string[];
    /**
     * Extra config merged in last; an escape hatch for per-repo tweaks.
     *
     * `rules` is merged into the base rule set and `overrides` is appended to the generated
     * per-file overrides, so a caller relaxing one rule keeps the rest. Every other key replaces
     * its base counterpart outright.
     */
    overrides?: OxlintConfig;
}

/** Default ignore patterns for generated/build output. */
export const DefaultIgnorePatterns = [
    "**/out",
    "**/dist",
    "**/.docusaurus/**",
    "**/node_modules",
    "**/coverage",
    "**/storybook-static",
];

/**
 * Builds the complete oxlint configuration for an authentik package.
 *
 * Consumers use it directly from an `oxlint.config.ts`:
 *
 * ```ts
 * import { createOxlintConfig } from "@goauthentik/oxlint-config";
 * export default createOxlintConfig();
 * ```
 *
 * @param options Configuration options.
 *
 * @returns A complete oxlint config object (no `extends` required).
 */
export function createOxlintConfig(options: OxlintConfigOptions = {}): OxlintConfig {
    const {
        packageNamespace = "@goauthentik",
        react = false,
        lit = false,
        padding = false,
        ignorePatterns = DefaultIgnorePatterns,
        overrides = {},
    } = options;

    const reactDependencies = react ? (["react"] as const) : ([] as const);
    const plugins: OxlintConfig["plugins"] = ["typescript", "unicorn", "oxc", ...reactDependencies];

    const jsPlugins: ExternalPluginEntry[] = ["@goauthentik/oxlint-config/plugin"];

    if (lit) {
        jsPlugins.push(...WebComponentJsPlugins);
    }

    const rules: DummyRuleMap = {
        // JavaScript
        "eqeqeq": ["error", "always", { null: "ignore" }],
        "prefer-const": "warn",
        "object-shorthand": ["warn", "always"],
        "no-shadow": "off",
        "no-undef": "off",
        "no-unused-vars": [
            "warn",
            {
                fix: {
                    imports: "safe-fix",
                },

                args: "all",
                argsIgnorePattern: "^_",
                caughtErrors: "all",
                caughtErrorsIgnorePattern: "^_",
                destructuredArrayIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                ignoreRestSiblings: true,
            },
        ],

        // TypeScript — intentionally permissive (matches the prior ESLint config).
        "typescript/ban-ts-comment": ["warn", { "ts-ignore": "allow-with-description" }],
        "typescript/ban-types": "off",
        "typescript/no-empty-interface": "off",
        "typescript/no-explicit-any": "off",
        "typescript/no-misused-new": "off",
        "typescript/no-non-null-assertion": "off",
        "typescript/no-var-requires": "off",
        "typescript/no-require-imports": "off",
        ...(padding ? PaddingRules : {}),
        ...(lit ? WebComponentRules : {}),
    };

    const { rules: ruleOverrides, overrides: fileOverrides, ...configOverrides } = overrides;

    return {
        plugins,
        jsPlugins,
        categories: { correctness: "error" },
        ignorePatterns,
        ...configOverrides,
        rules: { ...rules, ...ruleOverrides },
        overrides: [...createRuntimeOverrides(packageNamespace), ...(fileOverrides ?? [])],
    };
}

export default createOxlintConfig;
