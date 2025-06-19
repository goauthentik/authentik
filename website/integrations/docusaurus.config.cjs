/**
 * @file CommonJS Docusaurus config adapter.
 *
 * This exists to allow an ESM Docusaurus configuration to be imported in a CommonJS.
 *
 * @import Config from "./docusaurus.config.esm.mjs"
 */

/**
 * @see {@linkcode Config} for the Docusaurus configuration type.
 */
module.exports = import("./docusaurus.config.esm.mjs").then(($) => $.default);
