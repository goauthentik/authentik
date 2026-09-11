/**
 * @file Oxfmt configuration.
 */

import { authentikOxfmtConfig, DefaultIgnorePatterns } from "@goauthentik/oxfmt-config";

export default {
    ...authentikOxfmtConfig,
    ignorePatterns: [
        ...DefaultIgnorePatterns,
        "**/reference",
        "help/**",
        "static/**",
        "scripts/docsmg/target/**",
    ],
};
