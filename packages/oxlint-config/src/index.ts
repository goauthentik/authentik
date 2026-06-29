import { createRuntimeOverrides } from "./restrictions.js";

export * from "./restrictions.js";

export type OxlintConfig = Record<string, unknown>;

export interface OxlintConfigOptions {
    /** The package namespace whose runtime boundaries are enforced, e.g. `@goauthentik`. */
    packageNamespace?: string;
    /** Enable oxlint's React plugin (off by default). */
    react?: boolean;
    /** Override the default ignore patterns. */
    ignorePatterns?: string[];
    /** Extra config deep-merged last; an escape hatch for per-repo tweaks. */
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
 * import { createOxlintConfig } from "@goauthentik/oxlint-config"
 * export default createOxlintConfig()
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
        ignorePatterns = DefaultIgnorePatterns,
        overrides = {},
    } = options;

    const plugins = ["typescript", "unicorn", "oxc", ...(react ? ["react"] : [])];

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
        "goauthentik/padding-lines": "warn",
    };

    return {
        plugins,
        jsPlugins: ["@goauthentik/oxlint-config/plugin"],
        categories: { correctness: "error" },
        ignorePatterns,
        rules,
        overrides: createRuntimeOverrides(packageNamespace),
        ...overrides,
    };
}

export default createOxlintConfig;
