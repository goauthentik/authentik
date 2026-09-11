import { PaddingRules } from "./padding-rules.js";
import { createRuntimeOverrides } from "./restrictions.js";
import { WebComponentJsPlugins, WebComponentRules } from "./web-components.js";

export * from "./padding-rules.js";
export * from "./restrictions.js";
export * from "./web-components.js";

export type OxlintConfig = Record<string, unknown>;

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
    /** Extra config deep-merged last; an escape hatch for per-repo tweaks. */
    overrides?: OxlintConfig;
}

/**
 * Default ignore patterns for generated and build output.
 *
 * Carried over from the former `@goauthentik/eslint-config`: the generated locale bundles and API
 * client are checked in but never hand-edited, so linting them only produces noise.
 */
export const DefaultIgnorePatterns = [
    "**/out",
    "**/dist",
    "**/build/**",
    "**/.docusaurus/**",
    "**/.wireit",
    "**/node_modules",
    "**/coverage",
    "**/storybook-static",
    // Generated: `lit-localize extract` owns these.
    "**/locale-codes.ts",
    "**/src/locales",
    // Generated: `make gen-clients` owns this.
    "packages/client-ts",
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

    const plugins = ["typescript", "unicorn", "oxc", ...(react ? ["react"] : [])];

    const jsPlugins: unknown[] = ["@goauthentik/oxlint-config/plugin"];

    if (lit) {
        jsPlugins.push(...WebComponentJsPlugins);
    }

    const rules: Record<string, unknown> = {
        // JavaScript
        "eqeqeq": ["error", "always", { null: "ignore" }],
        "prefer-const": "warn",
        "object-shorthand": ["warn", "always"],
        "no-shadow": "off",
        "no-undef": "off",
        "no-unused-vars": [
            "warn",
            {
                args: "all",
                argsIgnorePattern: "^_",
                caughtErrors: "all",
                caughtErrorsIgnorePattern: "^_",
                destructuredArrayIgnorePattern: "^_",
                // Matches the prior ESLint config: unused vars are not reported (Prettier/oxfmt and TS
                // already cover most cases); only unused args without a `_` prefix are flagged.
                varsIgnorePattern: "^\\w",
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

    return {
        plugins,
        jsPlugins,
        categories: { correctness: "error" },
        ignorePatterns,
        rules,
        overrides: createRuntimeOverrides(packageNamespace),
        ...overrides,
    };
}

export default createOxlintConfig;
