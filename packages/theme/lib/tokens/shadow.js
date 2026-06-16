/**
 * @file Shadow tokens — sm..xl drop shadows and an inset variant.
 *
 * Dark theme uses higher opacity to read against the deeper backgrounds. The
 * inset shadow uses a near-solid color in dark mode rather than a faded rgba.
 */

import { theme, variable } from "../shared.js";

export const shadowSm = variable(
    "shadow.sm",
    "0 0.0625rem 0.125rem 0 rgba(3, 3, 3, 0.12), 0 0 0.125rem 0 rgba(3, 3, 3, 0.06)",
);
export const shadowMd = variable(
    "shadow.md",
    "0 0.25rem 0.5rem 0rem rgba(3, 3, 3, 0.12), 0 0 0.25rem 0 rgba(3, 3, 3, 0.06)",
);
export const shadowLg = variable(
    "shadow.lg",
    "0 0.5rem 1rem 0 rgba(3, 3, 3, 0.16), 0 0 0.375rem 0 rgba(3, 3, 3, 0.08)",
);
export const shadowXl = variable(
    "shadow.xl",
    "0 0.75rem 1.5rem 0 rgba(3, 3, 3, 0.2), 0 0 0.5rem 0 rgba(3, 3, 3, 0.1)",
);
export const shadowInset = variable("shadow.inset", "inset 0 0 0.625rem 0 rgba(3, 3, 3, 0.25)");

theme("dark", (ctx) => {
    ctx.variable(
        shadowSm,
        "0 0.0625rem 0.125rem 0 rgba(3, 3, 3, 0.48), 0 0 0.125rem 0 rgba(3, 3, 3, 0.24)",
    );
    ctx.variable(
        shadowMd,
        "0 0.25rem 0.5rem 0rem rgba(3, 3, 3, 0.48), 0 0 0.25rem 0 rgba(3, 3, 3, 0.24)",
    );
    ctx.variable(
        shadowLg,
        "0 0.5rem 1rem 0 rgba(3, 3, 3, 0.64), 0 0 0.375rem 0 rgba(3, 3, 3, 0.32)",
    );
    ctx.variable(
        shadowXl,
        "0 0.75rem 1.5rem 0 rgba(3, 3, 3, 0.8), 0 0 0.5rem 0 rgba(3, 3, 3, 0.4)",
    );
    ctx.variable(shadowInset, "inset 0 0 0.625rem 0 #030303");
});
