/**
 * @file Styleframe CLI entry point.
 *
 * The styleframe CLI (used by `npm run build:dtcg`) loads this file via jiti
 * and expects a default export that is a configured {@link Styleframe} instance
 * with all variables/themes already registered.
 *
 * Importing `./lib/tokens/index.js` triggers the side-effects that register
 * every token against the shared instance; we re-export `instance` as the
 * default export so the CLI's `dtcg export` and `build` commands operate on
 * the same tree the rest of the package uses.
 */

import "./src/tokens/index.js";

import { instance } from "./src/shared.js";

export default instance;
