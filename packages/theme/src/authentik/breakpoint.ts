/**
 * @file Shape tokens — border radii and stroke widths.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useBreakpoint = createUseVariable("breakpoint");

export const breakpoint = useBreakpoint(instance, {
    "xs": "0",
    "sm": "576px",
    "md": "768px",
    "lg": "992px",
    "xl": "1200px",
    "2xl": "1450px",
});

const useHeightBreakpoint = createUseVariable("height-breakpoint");

export const heightBreakpoint = useHeightBreakpoint(instance, {
    "sm": "0",
    "md": "40rem",
    "lg": "48rem",
    "xl": "60rem",
    "2xl": "80rem",
});
