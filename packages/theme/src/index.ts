/**
 * @file Public entry point for `@goauthentik/theme`.
 *
 * Importing this module registers every token against the shared styleframe
 * instance and re-exports the handles + primitives consumers need to author
 * component styles or build CSS.
 *
 * Browser-safe: no Node-only dependencies. Build helpers that touch the
 * filesystem live in `./lib/node.js` (exposed via the `./build` subpath).
 */

export { instance, ref, selector, theme, variable } from "./shared.js";
export * from "./tokens/index.js";
