/**
 * @file Font-family tokens — the concrete brand typefaces.
 *
 * Names authentik's font stacks: the variable RedHat faces, then platform
 * fallbacks. The semantic typography tokens (`font.family-body/heading/code`)
 * alias these, and the PatternFly bridge maps `--pf-global--FontFamily--*` onto
 * the semantic layer.
 *
 * The `@font-face` rules that bind these names to real files live in
 * `@goauthentik/fonts` — this package ships no font bytes, so a consumer that
 * does not load those faces falls through to the platform fallbacks.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useFontFamily = createUseVariable("font-family");

export const fontFamily = useFontFamily(instance, {
    "sans-serif": '"RedHatText", helvetica, arial, sans-serif',
    "display": '"RedHatDisplay", helvetica, arial, sans-serif',
    "monospace":
        '"RedHatMono", "Liberation Mono", consolas, "SFMono-Regular", menlo, monaco, "Courier New", monospace',
});
