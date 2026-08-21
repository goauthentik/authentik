/**
 * @file Spacing tokens — single scale from xs (4px) to 4xl (80px) at 16px base.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useGutters = createUseVariable("gutter");

export const gutter = useGutters(instance, {
    "": "1rem",
    "md": "1.5rem",
});
