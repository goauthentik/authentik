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

import { useColorDesignTokens, oklchTransform, type VPPair } from "./color-libs.js";
import { instance, theme, ref } from "../shared.js";

export const colors = useColorDesignTokens(instance, {
    "accent": "#fd4b2d",
    "primary": "#0066cc",
    "primary-hover": "#004080",
    "text": "#151515",
    "text-muted": "#6a6e73",
    "link": ref("primary"),
    "link-hover": ref("primary-hover"),
    "link-visited": "#40199a",
    "surface": "#ffffff",
    "surface-raised": "#fafafa",
    "surface-muted": "#f0f0f0",
    "border": "#d2d2d2",
    "border-strong": "#8a8d90",
    "info": "#2b9af3",
    "success": "#3e8635",
    "warning": "#f0ab00",
    "danger": "#c9190b",
});


// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the legacy drawer surface (#18191a) — the
// earlier oklab(0.23) value visibly brightened every PF-backed dark panel.
theme("dark", (ctx) => {
    const c = colors;
    
    const darkColors: VPPair[] = [
        [c.colorText, "#e0e0e0"],
        [c.colorTextMuted, "#aaabac"],
        [c.colorLink, "#20a9f8"],
        [c.colorLinkHover, "#73bcf7"],
        [c.colorLinkVisited, "#a18fff"],
        [c.colorSurface, "#121212"],
        [c.colorSurfaceMuted, "#090909"],
        [c.colorSurfaceRaised, "#1c1c1c"],
        [c.colorBorder, "#444548"],
        [c.colorBorderStrong, "#57585a"],
        [c.colorInfo, "#73bcf7"],
        [c.colorSuccess, "#5ba352"]
    ];

    darkColors.forEach(([v, p]) => ctx.variable(v, oklchTransform(p)));
});
