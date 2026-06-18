/**
 * @file Font tokens — font families
 *
 * Font families fall through to generic CSS `var(...)` references defined
 * upstream by the existing `fonts.css`. Sizes follow a modular xs..4xl scale.
 * `semi-bold` is deliberately omitted from the public surface because
 * PatternFly's `--pf-global--FontWeight--semi-bold` collapses to 700 (same as
 * bold) unless the Overpass font scale is active.
 */

import { variable } from "../shared.js";

import { theme, instance } from "../shared.js";
import { createUseVariable } from "@styleframe/theme";

const useFontFamily = createUseVariable("font-family");

export const fontFamily = useFontFamily(instance, {
    "text": '"RedHatTextVF", "RedHatText", helvetica, arial, sans-serif',
    "heading": '"RedHatDisplayVF", "RedHatDisplay", helvetica, arial, sans-serif',
    "monospace": '"RedHatMonoVF", "RedHatMono", "Liberation Mono", consolas, "SFMono-Regular", menlo, monaco, "Courier New", monospace'
});

