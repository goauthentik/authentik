/**
 * @file oxfmt configuration for authentik projects.
 */

import { OxfmtConfig } from "oxfmt";


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
    printWidth: 120,
    semi: true,
    trailingComma: "es5",
    bracketSpacing: true,
    jsdoc: {
        commentLineStrategy: "keep",
        separateReturnsFromParam: true,
    },
    sortPackageJson: true,
    sortImports: true,
};

export default authentikOxfmtConfig;
