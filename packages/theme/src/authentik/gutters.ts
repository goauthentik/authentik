/**
 * @file Gutter tokens — the horizontal inset a page frame reserves at its edges.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useGutters = createUseVariable("gutter");

export const gutter = useGutters(instance, {
    default: "1rem",
    md: "1.5rem",
});
