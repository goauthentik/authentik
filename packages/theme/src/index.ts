/**
 * @file Public entry point for `@goauthentik/theme`.
 *
 * Importing this module registers every token against the shared styleframe
 * instance and re-exports the handles + primitives consumers need to author
 * component styles or build CSS.
 *
 * Browser-safe: no Node-only dependencies. Build helpers that touch the
 * filesystem live in `./node.ts` (exposed via the `./build` subpath).
 *
 * **Do not sort these imports.** They are side-effect imports, and styleframe
 * validates an `@ref` the moment it is declared — referencing a variable that
 * has not been registered yet throws. So every authentik token module must run
 * before the patternfly bridge that points at it, and within each group a
 * module must follow whatever it references.
 */

import "./authentik/palette.js";
import "./authentik/background-color.js";
import "./authentik/spacing.js";
import "./authentik/gutters.js";
import "./authentik/motion.js";
import "./authentik/shape.js";
import "./authentik/shadow.js";
import "./authentik/fonts.js";
import "./authentik/icons.js";
import "./authentik/links.js";
import "./authentik/z-index.js";
import "./authentik/typography.js";
import "./authentik/breakpoint.js";
/*
 * The patternfly bridges
 */
import "./patternfly/palette.js";
import "./patternfly/background-color.js";
import "./patternfly/straight.js";
import "./patternfly/gutters.js";
import "./patternfly/motion.js";
import "./patternfly/shape.js";
import "./patternfly/fonts.js";
import "./patternfly/links.js";

import { instance } from "./shared.js";

export { instance };
