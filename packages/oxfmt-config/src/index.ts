/**
 * @file oxfmt configuration for authentik projects.
 */

import { OxfmtConfig } from "oxfmt";

import { authentikSortImportsConfig } from "./imports.js";

export * from "./imports.js";

/**
 * authentik's oxfmt configuration.
 *
 * ```ts
 * import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config"
 * export default { ...authentikOxfmtConfig }
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
        commentLineStrategy: "keep",
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

export default authentikOxfmtConfig;
