/**
 * @file Oxfmt configuration.
 */

import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config";
import { DefaultIgnorePatterns } from "@goauthentik/oxlint-config";

export default {
    ...authentikOxfmtConfig,
    // The fixtures are deliberately mis-formatted inputs for `scripts/verify-fixtures.mjs`.
    ignorePatterns: [...DefaultIgnorePatterns, "fixtures/**"],
};
