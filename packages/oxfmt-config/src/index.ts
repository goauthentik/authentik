/**
 * @file Oxfmt configuration for authentik projects.
 */

import { authentikSortImportsConfig } from "./imports.js";

import { OxfmtConfig } from "oxfmt";

export * from "./imports.js";

/**
 * authentik's oxfmt configuration.
 *
 * ```ts
 * import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config";
 * export default { ...authentikOxfmtConfig };
 * ```
 */
export const authentikOxfmtConfig: OxfmtConfig = {
    useTabs: false,
    tabWidth: 4,
    printWidth: 100,
    semi: true,
    trailingComma: "all",
    bracketSpacing: true,
    quoteProps: "consistent",
    jsdoc: {
        // The product name is always lowercase `authentik`, even sentence-initially.
        capitalizeDescriptions: false,
        commentLineStrategy: "keep",
        lineWrappingStyle: "balance",
        separateReturnsFromParam: true,
    },
    sortPackageJson: true,
    sortImports: authentikSortImportsConfig,
    // File-specific overrides carried over verbatim from the former `@goauthentik/prettier-config`.
    overrides: [
        // JSON Schemas are conventionally two-space indented.
        { files: ["schemas/**/*.json"], options: { tabWidth: 2 } },
        // `tsconfig.json` and other JSONC files must not carry trailing commas.
        { files: ["tsconfig.json", "*.jsonc"], options: { trailingComma: "none" } },
    ],
};

/** Default ignore patterns for generated/build output. */
export const DefaultIgnorePatterns = [
    "**/out",
    "**/dist",
    "**/.docusaurus/**",
    "**/node_modules",
    "**/coverage",
    "**/storybook-static",
];

export interface OxfmtConfigOptions {
    /** Override the default ignore patterns. */
    ignorePatterns?: string[];
    /**
     * Extra config merged in last; an escape hatch for per-repo tweaks.
     *
     * `overrides` is appended to the shared per-file overrides, so a caller adding one keeps the
     * rest. Every other key replaces its base counterpart outright.
     */
    overrides?: OxfmtConfig;
}

/**
 * Builds the complete oxfmt configuration for an authentik package.
 *
 * Consumers use it directly from an `oxfmt.config.ts`:
 *
 * ```ts
 * import { createOxfmtConfig } from "@goauthentik/oxfmt-config";
 * export default createOxfmtConfig();
 * ```
 *
 * @param options Configuration options.
 *
 * @returns A complete oxfmt config object.
 */
export function createOxfmtConfig(options: OxfmtConfigOptions = {}): OxfmtConfig {
    const { ignorePatterns = DefaultIgnorePatterns, overrides = {} } = options;
    const { overrides: fileOverrides, ...configOverrides } = overrides;

    return {
        ...authentikOxfmtConfig,
        ignorePatterns,
        ...configOverrides,
        overrides: [...(authentikOxfmtConfig.overrides ?? []), ...(fileOverrides ?? [])],
    };
}

export default createOxfmtConfig;
