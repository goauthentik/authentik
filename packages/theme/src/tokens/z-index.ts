/**
 * @file Z-index tokens — xs..2xl tiers matching PatternFly 4's scale.
 *
 * Spelled out as `z-index.*` rather than `z.*` so the emitted CSS
 * (`--ak-z-index-md`) is unambiguous in brand custom CSS and IDE
 * autocomplete.
 */

import { variable } from "../shared.js";

export const zIndexXs = variable("z-index.xs", 100);
export const zIndexSm = variable("z-index.sm", 200);
export const zIndexMd = variable("z-index.md", 300);
export const zIndexLg = variable("z-index.lg", 400);
export const zIndexXl = variable("z-index.xl", 500);
export const zIndex2xl = variable("z-index.2xl", 600);
