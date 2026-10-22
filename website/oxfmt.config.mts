/**
 * @file Oxfmt configuration.
 */

import { createOxfmtConfig, DefaultIgnorePatterns } from "@goauthentik/oxfmt-config";

export default createOxfmtConfig({
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
});
