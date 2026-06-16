/**
 * @file Color tokens — semantic surface, text, state, and brand colors.
 *
 * Light values are declared via `variable()`. Dark values are declared inside
 * the `dark` theme block so they emit under `html[data-theme="dark"]`.
 *
 * Link tokens are wired through `ref()` so brand overrides to `color.primary`
 * cascade to links without separate overrides. The dark theme intentionally
 * re-points links to their own oklab values rather than chaining through
 * primary because dark mode links need higher luminance than primary buttons.
 *
 * `warning` and `danger` deliberately stay on light values in dark mode — state
 * colors keep consistent intensity across themes so warnings read as urgent.
 */

import { ref, theme, variable } from "../shared.js";

export const colorAccent = variable("color.accent", "#fd4b2d");
export const colorPrimary = variable("color.primary", "oklab(0.522 -0.0434 -0.1717)");
export const colorPrimaryHover = variable("color.primary-hover", "oklab(0.3763 -0.0324 -0.1182)");
export const colorText = variable("color.text", "oklab(0.1957 -0 0)");
export const colorTextMuted = variable("color.text-muted", "oklab(0.5364 -0.0026 -0.0089)");

export const colorLink = variable("color.link", ref(colorPrimary));
export const colorLinkHover = variable("color.link-hover", ref(colorPrimaryHover));
export const colorLinkVisited = variable("color.link-visited", "oklab(0.3679 0.0535 -0.1797)");

export const colorSurface = variable("color.surface", "oklab(1 -0 0)");
export const colorSurfaceMuted = variable("color.surface-muted", "oklab(0.9551 -0 0)");
export const colorSurfaceRaised = variable("color.surface-raised", "oklab(0.9851 -0 0)");

export const colorBorder = variable("color.border", "#d2d2d2");
export const colorBorderStrong = variable("color.border-strong", "#8a8d90");

export const colorInfo = variable("color.info", "oklab(0.6689 -0.0608 -0.1513)");
export const colorSuccess = variable("color.success", "oklab(0.5549 -0.1071 0.0852)");
export const colorWarning = variable("color.warning", "oklab(0.7864 0.0298 0.1604)");
export const colorDanger = variable("color.danger", "oklab(0.5331 0.1798 0.1034)");

// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the legacy drawer surface (#18191a) — the
// earlier oklab(0.23) value visibly brightened every PF-backed dark panel.
theme("dark", (ctx) => {
    ctx.variable(colorText, "oklab(0.9067 -0 0)");
    ctx.variable(colorTextMuted, "oklab(0.7407 -0.0007 -0.0017)");
    ctx.variable(colorLink, "oklab(70.367% -0.07498 -0.139)");
    ctx.variable(colorLinkHover, "oklab(0.7706 -0.0485 -0.1012)");
    ctx.variable(colorLinkVisited, "oklab(0.7137 0.0522 -0.151)");
    ctx.variable(colorSurface, "oklab(0.183 -0 0)");
    ctx.variable(colorSurfaceMuted, "oklab(0.14 -0 0)");
    ctx.variable(colorSurfaceRaised, "oklab(0.225 -0 0)");
    ctx.variable(colorBorder, "oklab(0.3906 0.0001 -0.0052)");
    ctx.variable(colorBorderStrong, "oklab(0.4602 -0.0003 -0.0034)");
    ctx.variable(colorInfo, "oklab(0.7706 -0.0485 -0.1012)");
    ctx.variable(colorSuccess, "oklab(0.6488 -0.1066 0.0846)");
});
