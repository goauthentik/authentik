/**
 * @file Color tokens — semantic surface, text, state, and brand colors.
 *
 * Declared as an aligned table so the set stays scannable: find a token by its
 * row, read its CSS value in the same column every time. Light values live in
 * the `colors` table; dark values are declared inside the `dark` theme block so
 * they emit under `html[data-theme="dark"]`.
 *
 * `color.primary` anchors the link tokens through `ref()` so brand overrides to
 * primary cascade to links without separate overrides. Its handle and hover
 * variant are declared before the table that consumes them. The dark theme
 * intentionally re-points links to their own rgb values rather than chaining
 * through primary because dark mode links need higher luminance than primary
 * buttons.
 *
 * `warning` and `danger` deliberately stay on light values in dark mode — state
 * colors keep consistent intensity across themes so warnings read as urgent.
 */

import { ref, theme, variable } from "../shared.js";

const colorPrimary = variable("color.primary", "rgb(0, 102, 204)");
const colorPrimaryHover = variable("color.primary-hover", "rgb(0, 64, 128)");

// prettier-ignore
export const colors = {
    colorPrimary,
    colorPrimaryHover,
    colorAccent:        variable("color.accent",         "rgb(253, 75, 45)"),
    colorText:          variable("color.text",           "rgb(21, 21, 21)"),
    colorTextMuted:     variable("color.text-muted",     "rgb(106, 110, 115)"),

    colorLink:          variable("color.link",           ref(colorPrimary)),
    colorLinkHover:     variable("color.link-hover",     ref(colorPrimaryHover)),
    colorLinkVisited:   variable("color.link-visited",   "rgb(64, 25, 154)"),

    colorSurface:       variable("color.surface",        "rgb(255, 255, 255)"),
    colorSurfaceMuted:  variable("color.surface-muted",  "rgb(240, 240, 240)"),
    colorSurfaceRaised: variable("color.surface-raised", "rgb(250, 250, 250)"),

    colorBorder:        variable("color.border",         "rgb(210, 210, 210)"),
    colorBorderStrong:  variable("color.border-strong",  "rgb(138, 141, 144)"),

    colorInfo:          variable("color.info",           "rgb(43, 154, 243)"),
    colorSuccess:       variable("color.success",        "rgb(62, 134, 53)"),
    colorWarning:       variable("color.warning",        "rgb(240, 171, 0)"),
    colorDanger:        variable("color.danger",         "rgb(201, 25, 11)"),
};

export default colors;

// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the legacy drawer surface (#18191a) — the
// earlier brighter surface value visibly washed out every PF-backed dark panel.
// prettier-ignore
theme("dark", (ctx) => {
    ctx.variable(colors.colorText,          "rgb(224, 224, 224)");
    ctx.variable(colors.colorTextMuted,     "rgb(170, 171, 172)");
    ctx.variable(colors.colorLink,          "rgb(32, 169, 248)");
    ctx.variable(colors.colorLinkHover,     "rgb(115, 188, 247)");
    ctx.variable(colors.colorLinkVisited,   "rgb(161, 143, 255)");
    ctx.variable(colors.colorSurface,       "rgb(18, 18, 18)");
    ctx.variable(colors.colorSurfaceMuted,  "rgb(9, 9, 9)");
    ctx.variable(colors.colorSurfaceRaised, "rgb(28, 28, 28)");
    ctx.variable(colors.colorBorder,        "rgb(68, 69, 72)");
    ctx.variable(colors.colorBorderStrong,  "rgb(87, 88, 90)");
    ctx.variable(colors.colorInfo,          "rgb(115, 188, 247)");
    ctx.variable(colors.colorSuccess,       "rgb(91, 163, 82)");
});
