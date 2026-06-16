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

import { instance, theme } from "../shared.js";

import { createVariableFunction } from "styleframe";
import { createUseVariable } from "@styleframe/theme";
import { formatHex, oklch as toOklch, toGamut } from "culori";

/*
 * Restrict the OKLCH values to six decimal places; Javascript will give it to you accurate to 16
 * places, but OKLCH doesn't much care past six, and 16 is just unreadable.
 *
 * Includes in each OKLCH output line a comment containing the RGB value, to help IDEs show the
 * color accurately.
 */


const toSrgb = toGamut("rgb", "oklch");
const round = (v: number, precision = 6) => Number(v.toFixed(precision)).toString();
const oklchTransform = (value: string) => {
        const c = toOklch(value);
        if (!c || c.l == null || c.c == null) {
            return value;
        }

        const result = `oklch(${round(c.l)} ${round(c.c)} ${round(c.h ?? 0)} / ${round(c.alpha ?? 1)})`;
        return `${result} /* ${formatHex(toSrgb(c))} */`;
};
const useColorDesignTokens = createUseVariable("color", { transform: oklchTransform });

export const {
    colorAccent,
    colorPrimary,
    colorPrimaryHover,
    colorText,
    colorTextMuted,
    colorLink,
    colorLinkHover,
    colorLinkVisited,
    colorSurface,
    colorSurfaceRaised,
    colorSurfaceMuted,
    colorBorder,
    colorBorderStrong,
    colorInfo,
    colorSuccess,
    colorWarning,
    colorDanger,
} = useColorDesignTokens(instance, {
    "accent": "#fd4b2d",
    "primary": "#0066cc",
    "primary-hover": "#004080",
    "text": "#151515",
    "text-muted": "#6a6e73",
    "link": "@color.primary",
    "link-hover": "@color.primary-hover",
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

type Variable = ReturnType<ReturnType<typeof createVariableFunction>>;
type VPPair = [Variable, string];

// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the legacy drawer surface (#18191a) — the
// earlier oklab(0.23) value visibly brightened every PF-backed dark panel.
theme("dark", (ctx) => {

    const darkColors: VPPair[] = [
        [colorText, "#e0e0e0"],
        [colorTextMuted, "#aaabac"],
        [colorLink, "#20a9f8"],
        [colorLinkHover, "#73bcf7"],
        [colorLinkVisited, "#a18fff"],
        [colorSurface, "#121212"],
        [colorSurfaceMuted, "#090909"],
        [colorSurfaceRaised, "#1c1c1c"],
        [colorBorder, "#444548"],
        [colorBorderStrong, "#57585a"],
        [colorInfo, "#73bcf7"],
        [colorSuccess, "#5ba352"]
    ];

    darkColors.forEach(([v, p]) => ctx.variable(v, oklchTransform(p)));
});
