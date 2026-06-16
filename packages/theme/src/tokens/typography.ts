/**
 * @file Typography tokens — font families, sizes, line heights, weights.
 *
 * Font families fall through to generic CSS `var(...)` references defined
 * upstream by the existing `fonts.css`. Sizes follow a modular xs..4xl scale.
 * `semi-bold` is deliberately omitted from the public surface because
 * PatternFly's `--pf-global--FontWeight--semi-bold` collapses to 700 (same as
 * bold) unless the Overpass font scale is active.
 */

import { variable } from "../shared.js";

export const fontFamilyBody = variable("font.family-body", "var(--ak-font-family-sans-serif)");
export const fontFamilyHeading = variable("font.family-heading", "var(--ak-generic-display)");
export const fontFamilyCode = variable("font.family-code", "var(--ak-font-family-monospace)");

export const fontSizeXs = variable("font.size-xs", "0.75rem");
export const fontSizeSm = variable("font.size-sm", "0.875rem");
export const fontSizeMd = variable("font.size-md", "1rem");
export const fontSizeLg = variable("font.size-lg", "1.125rem");
export const fontSizeXl = variable("font.size-xl", "1.25rem");
export const fontSize2xl = variable("font.size-2xl", "1.5rem");
export const fontSize3xl = variable("font.size-3xl", "1.75rem");
export const fontSize4xl = variable("font.size-4xl", "2.25rem");

export const fontWeightLight = variable("font.weight-light", 300);
export const fontWeightNormal = variable("font.weight-normal", 400);
export const fontWeightBold = variable("font.weight-bold", 700);

export const lineHeightSm = variable("line-height.sm", 1.3);
export const lineHeightMd = variable("line-height.md", 1.5);
