/**
 * @file Shadow tokens — sm..xl drop shadows and an inset variant.
 *
 * Dark theme uses higher opacity to read against the deeper backgrounds. The
 * inset shadow uses a near-solid color in dark mode rather than a faded rgba.
 */

import { theme, instance } from "../shared.js";
import { createUseVariable } from "@styleframe/theme";
import type { VPPair } from "./color-libs.js";
const useShadowTokens = createUseVariable("shadow");

export const shadow = useShadowTokens(instance, {
    sm: "0 0.0625rem 0.125rem 0 rgba(3, 3, 3, 0.12), 0 0 0.125rem 0 rgba(3, 3, 3, 0.06)",
    md: "0 0.25rem 0.5rem 0rem rgba(3, 3, 3, 0.12), 0 0 0.25rem 0 rgba(3, 3, 3, 0.06)",
    lg: "0 0.5rem 1rem 0 rgba(3, 3, 3, 0.16), 0 0 0.375rem 0 rgba(3, 3, 3, 0.08)",
    xl: "0 0.75rem 1.5rem 0 rgba(3, 3, 3, 0.2), 0 0 0.5rem 0 rgba(3, 3, 3, 0.1)",
    inset: "inset 0 0 0.625rem 0 rgba(3, 3, 3, 0.25)"
});

theme("dark", (ctx) => {
    const s = shadow;
    const darkShadows: VPPair[] = [
        [s.shadowSm, "0 0.0625rem 0.125rem 0 rgba(3, 3, 3, 0.48), 0 0 0.125rem 0 rgba(3, 3, 3, 0.24)"],
        [s.shadowMd, "0 0.25rem 0.5rem 0rem rgba(3, 3, 3, 0.48), 0 0 0.25rem 0 rgba(3, 3, 3, 0.24)"],
        [s.shadowLg, "0 0.5rem 1rem 0 rgba(3, 3, 3, 0.64), 0 0 0.375rem 0 rgba(3, 3, 3, 0.32)"],
        [s.shadowXl, "0 0.75rem 1.5rem 0 rgba(3, 3, 3, 0.8), 0 0 0.5rem 0 rgba(3, 3, 3, 0.4)"],
        [s.shadowInset, "inset 0 0 0.625rem 0 #030303"]
    ];

    darkShadows.forEach(([v, p]) => ctx.variable(v, p));
});
