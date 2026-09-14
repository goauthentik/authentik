/**
 * @file Z-index tokens — xs..2xl tiers matching PatternFly 4's scale.
 *
 * Spelled out as `z-index.*` rather than `z.*` so the emitted CSS
 * (`--ak-z-index-md`) is unambiguous in brand custom CSS and IDE
 * autocomplete.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useZIndex = createUseVariable("z-index");

export const zIndex = useZIndex(instance, {
    "xs": 100,
    "sm": 200,
    "md": 300,
    "lg": 400,
    "xl": 500,
    "2xl": 600,
});
