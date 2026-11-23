/**
 * @file Oxfmt configuration.
 */

import { createOxfmtConfig, DefaultIgnorePatterns } from "@goauthentik/oxfmt-config";

export default createOxfmtConfig({
    // The fixtures are deliberately mis-formatted inputs for `scripts/verify-fixtures.mjs`.
    ignorePatterns: [...DefaultIgnorePatterns, "fixtures/**"],
});
