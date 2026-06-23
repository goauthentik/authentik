/**
 * @file Color tokens — semantic surface, text, state, and brand colors.
 *
 * Light values are declared via `variable()`. Dark values are declared inside
 * the `dark` theme block so they emit under `html[data-theme="dark"]`.
 *
 * Link tokens are wired through `ref()` so brand overrides to `color.primary`
 * cascade to links without separate overrides. The dark theme intentionally
 * re-points links to their own rgb values rather than chaining through
 * primary because dark mode links need higher luminance than primary buttons.
 *
 * `warning` and `danger` deliberately stay on light values in dark mode — state
 * colors keep consistent intensity across themes so warnings read as urgent.
 */

import { ref, theme, variable } from "../shared.js";

export const colorAccent = variable("color.accent", "rgb(253, 75, 45)");
export const colorPrimary = variable("color.primary", "rgb(0, 102, 204)");
export const colorPrimaryHover = variable("color.primary-hover", "rgb(0, 64, 128)");
export const colorText = variable("color.text", "rgb(21, 21, 21)");
export const colorTextMuted = variable("color.text-muted", "rgb(106, 110, 115)");

export const colorLink = variable("color.link", ref(colorPrimary));
export const colorLinkHover = variable("color.link-hover", ref(colorPrimaryHover));
export const colorLinkVisited = variable("color.link-visited", "rgb(64, 25, 154)");

export const colorSurface = variable("color.surface", "rgb(255, 255, 255)");
export const colorSurfaceMuted = variable("color.surface-muted", "rgb(240, 240, 240)");
export const colorSurfaceRaised = variable("color.surface-raised", "rgb(250, 250, 250)");

export const colorBorder = variable("color.border", "rgb(210, 210, 210)");
export const colorBorderStrong = variable("color.border-strong", "rgb(138, 141, 144)");

export const colorInfo = variable("color.info", "rgb(43, 154, 243)");
export const colorSuccess = variable("color.success", "rgb(62, 134, 53)");
export const colorWarning = variable("color.warning", "rgb(240, 171, 0)");
export const colorDanger = variable("color.danger", "rgb(201, 25, 11)");

// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the legacy drawer surface (#18191a) — the
// earlier brighter surface value visibly washed out every PF-backed dark panel.
theme("dark", (ctx) => {
    ctx.variable(colorText, "rgb(224, 224, 224)");
    ctx.variable(colorTextMuted, "rgb(170, 171, 172)");
    ctx.variable(colorLink, "rgb(32, 169, 248)");
    ctx.variable(colorLinkHover, "rgb(115, 188, 247)");
    ctx.variable(colorLinkVisited, "rgb(161, 143, 255)");
    ctx.variable(colorSurface, "rgb(18, 18, 18)");
    ctx.variable(colorSurfaceMuted, "rgb(9, 9, 9)");
    ctx.variable(colorSurfaceRaised, "rgb(28, 28, 28)");
    ctx.variable(colorBorder, "rgb(68, 69, 72)");
    ctx.variable(colorBorderStrong, "rgb(87, 88, 90)");
    ctx.variable(colorInfo, "rgb(115, 188, 247)");
    ctx.variable(colorSuccess, "rgb(91, 163, 82)");
});
