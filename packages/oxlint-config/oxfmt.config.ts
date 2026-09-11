/**
 * @file Oxfmt configuration.
 */

import { authentikOxfmtConfig, DefaultIgnorePatterns } from "@goauthentik/oxfmt-config";

export default {
    ...authentikOxfmtConfig,
    ignorePatterns: [...DefaultIgnorePatterns, "fixtures/**"],
};
