/**
 * @file Oxlint configuration.
 */

import { createOxlintConfig, DefaultIgnorePatterns } from "@goauthentik/oxlint-config";

export default createOxlintConfig({
    ignorePatterns: [
        ...DefaultIgnorePatterns,
        "**/fixtures/**",
        "docs/**",
    ],
});
