/**
 * @file Font-family tokens — the concrete brand typefaces.
 *
 * Self-contained source of authentik's font stacks: the variable RedHat faces
 * first (registered in `font-face.css`), then the static RedHat faces, then
 * platform fallbacks. The semantic typography tokens
 * (`font.family-body/heading/code`) alias these, and the PatternFly bridge maps
 * `--pf-global--FontFamily--*` onto the semantic layer. Because the stacks are
 * declared here rather than referenced from a consumer's stylesheet, the
 * package resolves fonts on its own once published.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useFontFamily = createUseVariable("font-family");

export const fontFamily = useFontFamily(instance, {
    "sans-serif": '"RedHatTextVF", "RedHatText", helvetica, arial, sans-serif',
    "display": '"RedHatDisplayVF", "RedHatDisplay", helvetica, arial, sans-serif',
    "monospace":
        '"RedHatMonoVF", "RedHatMono", "Liberation Mono", consolas, "SFMono-Regular", menlo, monaco, "Courier New", monospace',
});
