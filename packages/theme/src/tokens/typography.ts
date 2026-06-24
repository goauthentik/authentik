/**
 * @file Typography tokens — font families, sizes, line heights, weights.
 *
 * The semantic family tokens (body/heading/code) alias the concrete brand
 * stacks declared in `./fonts.ts` (`--ak-font-family-sans-serif/display/
 * monospace`), so the package resolves fonts on its own. Sizes follow a
 * modular xs..4xl scale. `semi-bold` is deliberately omitted from the public
 * surface because
 * PatternFly's `--pf-global--FontWeight--semi-bold` collapses to 700 (same as
 * bold) unless the Overpass font scale is active.
 */

import { instance, variable } from "../shared.js";

import { useFontSizeDesignTokens } from "@styleframe/theme";

export const fontFamilyBody = variable("font.family-body", "var(--ak-font-family-sans-serif)");
export const fontFamilyHeading = variable("font.family-heading", "var(--ak-font-family-display)");
export const fontFamilyCode = variable("font.family-code", "var(--ak-font-family-monospace)");

export const fontSize = useFontSizeDesignTokens(instance, {
    "xs": "0.75rem",
    "sm": "0.875rem",
    "md": "1rem",
    "lg": "1.125rem",
    "xl": "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.75rem",
    "4xl": "2.25rem",
});

export const fontWeightLight = variable("font.weight-light", 300);
export const fontWeightNormal = variable("font.weight-normal", 400);
export const fontWeightBold = variable("font.weight-bold", 700);

export const lineHeightSm = variable("line-height.sm", 1.3);
export const lineHeightMd = variable("line-height.md", 1.5);
