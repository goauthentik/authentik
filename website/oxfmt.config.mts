/**
 * @file Oxfmt configuration.
 */

import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config";
import { DefaultIgnorePatterns } from "@goauthentik/oxlint-config";

export default {
    ...authentikOxfmtConfig,
    ignorePatterns: [
        ...DefaultIgnorePatterns,
        "**/reference",
        "help/**",
        "static/**",
        "scripts/docsmg/target/**",
        "build",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
    ],
};
