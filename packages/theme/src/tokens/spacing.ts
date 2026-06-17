/**
 * @file Spacing tokens — single scale from xs (4px) to 4xl (80px) at 16px base.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useSpacing = createUseVariable("space");

export const space = useSpacing(instance, {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
    "3xl": "4rem",
    "4xl": "5rem",
});
