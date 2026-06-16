/**
 * @file Motion tokens — duration and easing.
 *
 * Reduced motion is expressed two ways. Both override `--ak-duration-normal`
 * to `0ms`:
 *
 * 1. `@media (prefers-reduced-motion: reduce)` — triggers automatically from
 *    the operating system's accessibility preference. This is the path most
 *    consumers actually hit.
 * 2. `html[data-theme="reduced"]` — opt-in via data attribute, for explicit
 *    forced-reduced-motion or for previewing the reduced state. This block
 *    exists primarily so the styleframe DTCG export can represent reduced
 *    motion as a theme modifier — DTCG has no native concept for media
 *    queries.
 *
 * The two emissions are independent and don't conflict; either one alone is
 * enough to zero the duration. Keeping both lets us roundtrip the reduced
 * state through DTCG-aware tooling without losing the automatic OS trigger.
 */

import { media, theme, variable } from "../shared.js";

export const durationNormal = variable("duration.normal", "250ms");
export const easingStandard = variable("easing.standard", "cubic-bezier(0.645, 0.045, 0.355, 1)");

media("(prefers-reduced-motion: reduce)", (ctx) => {
    ctx.selector(":root", (root) => {
        root.variable(durationNormal, "0ms");
    });
});

theme("reduced", (ctx) => {
    ctx.variable(durationNormal, "0ms");
});
