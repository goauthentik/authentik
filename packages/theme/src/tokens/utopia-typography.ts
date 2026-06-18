/**
 * @file Typography tokens — font families, sizes, line heights, weights.
 *
 * Font families fall through to generic CSS `var(...)` references defined
 * upstream by the existing `fonts.css`. Sizes follow a modular xs..4xl scale.
 * `semi-bold` is deliberately omitted from the public surface because
 * PatternFly's `--pf-global--FontWeight--semi-bold` collapses to 700 (same as
 * bold) unless the Overpass font scale is active.
 */

import { instance, variable } from "../shared.js";
import { useFontSizeDesignTokens } from "@styleframe/theme";
import { calculateTypeScale } from "utopia-core";

const utopiaSizes = calculateTypeScale({
  minWidth: 320,
  maxWidth: 1440,
  minFontSize: 14,
  maxFontSize: 18,
  minTypeScale: 1.125,
  maxTypeScale: 1.25,
  positiveSteps: 5,
  negativeSteps: 2
});

if (utopiaSizes === undefined) {
    throw new Error("Failed to parse utopiaScale configuration for utopia spacing.");
}

utopiaSizes.reverse();

const utopiaScaling = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl"].reduce((acc, s, idx) => {
    const size = utopiaSizes[idx];
    if (!size) {
        throw new Error("Scale elements out of range for utopia font sizing.");
    }
        
        return { ...acc, [s]: size.clamp };
},
    {}
);

export const fontSize = useFontSizeDesignTokens(instance, utopiaScaling);

export const fontWeightLight = variable("font.weight-light", 300);
export const fontWeightNormal = variable("font.weight-normal", 400);
export const fontWeightBold = variable("font.weight-bold", 700);

export const lineHeightSm = variable("line-height.sm", 1.3);
export const lineHeightMd = variable("line-height.md", 1.5);
