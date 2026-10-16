/**
 * @file Oxlint configuration.
 */

import { createOxlintConfig, DefaultIgnorePatterns } from "@goauthentik/oxlint-config";

export default createOxlintConfig({
    // The docusaurus theme is React, not Lit.
    react: true,
    ignorePatterns: [
        ...DefaultIgnorePatterns,
        "**/reference",
        "help/**",
        "static/**",
        "scripts/docsmg/target/**",
    ],
});
