/**
 * @file Oxlint configuration for the repository root. `web/`, `website/` and every package carry
 *   their own config, so the root scripts pass an explicit list of root-owned paths rather than
 *   sweeping the tree — see the `lint` scripts in package.json.
 */

import { createOxlintConfig } from "@goauthentik/oxlint-config";

export default createOxlintConfig();
