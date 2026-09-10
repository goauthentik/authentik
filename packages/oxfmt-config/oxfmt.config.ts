/**
 * @file Oxfmt configuration
 */

import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config";

export default {
    ...authentikOxfmtConfig,
    ignorePatterns: [
        "**/out",
        "**/dist",
        "**/node_modules",
        "**/*.md",
        "docs/**",
        "**/fixtures/**",
        "**/eslint-config/**",
        "**/prettier-config/**",
    ],
};
