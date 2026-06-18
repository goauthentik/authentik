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

export const fontFamilyBody = variable("font.family-body", "var(--ak-font-family-sans-serif)");
export const fontFamilyHeading = variable("font.family-heading", "var(--ak-generic-display)");
export const fontFamilyCode = variable("font.family-code", "var(--ak-font-family-monospace)");

