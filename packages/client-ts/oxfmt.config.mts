/**
 * @file Oxfmt configuration for the generated API client. The shared config lists
 *   `packages/client-ts` among its ignore patterns, so that other workspaces never reformat
 *   generated output. This one runs from inside that directory and is the exception: the generator
 *   writes `src/` unformatted, and `make gen-client-ts` formats it once on the way out.
 */

import { authentikOxfmtConfig } from "@goauthentik/oxfmt-config";

export default {
    ...authentikOxfmtConfig,
    // The generator writes a structured banner into every file. oxfmt's JSDoc pass reflows it into
    // run-on prose and re-cases the first word, which turns `authentik` into `Authentik` — the one
    // spelling this project never uses. Nothing here is hand-written documentation, so the pass has
    // nothing to gain and a 967-file diff to lose.
    jsdoc: false,
    ignorePatterns: ["**/node_modules", "**/dist", "**/out", "docs/**"],
};
