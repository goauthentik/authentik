/* eslint-disable sort-imports */
/**
 * @file Public entry point for `@goauthentik/theme`.
 *
 * Importing this module registers every token against the shared styleframe
 * instance and re-exports the handles + primitives consumers need to author
 * component styles or build CSS.
 *
 * Browser-safe: no Node-only dependencies. Build helpers that touch the
 * filesystem live in `./node.ts` (exposed via the `./build` subpath).
 */

import "./authentik/palette.js";
import "./authentik/background-color.js";
import "./authentik/spacing.js";
import "./authentik/gutters.js";
/*
 * The patternfly bridges
 */
import "./patternfly/palette.js";
import "./patternfly/background-color.js";
import "./patternfly/spacing.js";
import "./patternfly/gutters.js";

import { instance } from "./shared.js";

export { instance };
