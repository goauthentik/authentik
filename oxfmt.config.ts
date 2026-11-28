/**
 * @file Oxfmt configuration for the repository root.
 *   Scoped by the explicit paths the `format` scripts pass; see `oxlint.config.ts`.
 */

import { DefaultIgnorePatterns, createOxfmtConfig } from "@goauthentik/oxfmt-config";

export default createOxfmtConfig({
    // `*.json` in the format scripts' paths would otherwise pick up cspell's report.
    ignorePatterns: [...DefaultIgnorePatterns, "cspell-report.*"],
});
