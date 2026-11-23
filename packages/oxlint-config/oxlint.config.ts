/**
 * @file Oxlint configuration.
 */

import { createOxlintConfig, DefaultIgnorePatterns } from "@goauthentik/oxlint-config";

export default createOxlintConfig({
    // `fixtures/` holds deliberate rule violations for `scripts/verify-fixtures.mjs`. They are lint
    // subjects, not sources — linting them here would report every violation they exist to prove.
    ignorePatterns: [...DefaultIgnorePatterns, "fixtures/**"],
});
