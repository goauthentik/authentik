/**
 * @file Shape tokens — border radii and stroke widths.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useRadii = createUseVariable("radius");
const useBorders = createUseVariable("border-width");

export const radii = useRadii(instance, {
    sm: "3px",
    pill: "30em",
});

export const borders = useBorders(instance, {
    sm: "1px",
    md: "2px",
    lg: "3px",
    xl: "4px",
});
