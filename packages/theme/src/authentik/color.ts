/**
 * @file Color tokens — semantic surface, text, state, and brand colors.
 *
 * Light values are declared via `variable()`. Dark values are declared inside
 * the `dark` theme block so they emit under `html[data-theme="dark"]`.
 *
 * Link tokens are wired through `ref()` so brand overrides to `color.primary`
 * cascade to links without separate overrides. The dark theme intentionally
 * re-points links to their own values rather than chaining through primary
 * because dark mode links need higher luminance than primary buttons.
 *
 * `warning` and `danger` deliberately stay on light values in dark mode — state
 * colors keep consistent intensity across themes so warnings read as urgent.
 *
 * Values are authored as hex and transformed to `oklch()` on emit (see
 * `./color-libs.ts`). Read the maps below as a spreadsheet: one group per
 * concern, light values first, dark overrides in the theme block underneath.
 */

import { instance, theme } from "../shared.js";
import { oklchTransform, useColorDesignTokens, type VPPair } from "./color-libs.js";

// "pin-" means that the color is "pinned" to that color regardless of the mode. "pin-light" will
// always be content appropriate to a "light surface," regardless of the mode.

// prettier-ignore
export const colors = useColorDesignTokens(instance, {
    "accent": "#fd4b2d",  // authentik brand color.

    "ink":        "#151515",  // Color-100, everywhere
    "ink.muted":  "#6a6e73",  // Color-200, helper text, de-emphasized text
    "ink.subtle": "#8a8d90",  // Faintest ink, Color-400

    "ink.pin-light": "#151515",

    "ink.pin-dark":        "#ffffff",
    "ink.pin-dark.muted":  "#f0f0f0",
    "ink.pin-dark.subtle": "#d2d2d2",

    "ink.placeholder": "#6a6e73", 
    
    "link":         "@color.primary",
    "link.hover":   "@color.primary.active",
    "link.visited": "#40199a",

    "surface":        "#ffffff",  // BackgroundColor-100, Main Background
    "surface.raised": "#fafafa",  // BackgroundColor-150, 
    "surface.muted":  "#f0f0f0",  // BackgroundColor-200, 
    "surface.nested": "#f1f9ff",  // Unique to authentik

    "surface.pin-light":        "#ffffff",
    "surface.pin-light.raised": "#fafafa",
    "surface.pin-light.muted":  "#f0f0f0",

    "surface.pin-dark":        "#151515",
    "surface.pin-dark.raised": "#3c3f42",
    "surface.pin-dark.muted":  "#212427",

    "scrim":       "rgba(3, 3, 3, 0.62)",  // Heavy backdrop for modals
    "scrim.light": "rgba(3, 3, 3, 0.32)",  // Light backdrop for modals

    "border":        "#d2d2d2",
    "border.edge":   "#8a8d90",
    "border.subtle": "#f0f0f0",

    "border.pin-dark":  "#b8bbbe",
    "border.pin-light": "#d2d2d2",

    "primary":        "#0066cc", 
    "primary.active": "#004080", // Used for "pressed"

    "primary.pin-dark":  "#73bcf7",
    "primary.pin-light": "#0066cc",

    "active":       "#0066cc", // Selection indicator
    "active.fill":  "#bee1f4", // Fill color for controls
    "active.hover": "#2b9af3", // Hover indicator
    "active.hint":  "#73bcf7", // Hover borders

    "disabled": "",
    "disabled.fill": "",
    "disabled.readonly": "",

    "neutral":         "#009596",
    "neutral.fill":    "#f2f2f9",
    "neutral.surface": "#f2f2f9",
    "neutral.deep":    "#003737",

    "success": "#3e8635",
    "success.fill": "#f3faf2",
    "success.deep": "#1e4f18",
    "info": "#2b9af3",
    "info.fill": "#e7f1fa",
    "info.deep": "#002952",
    "warning": "#f0ab00",
    "warning.fill": "#fdf7e7",
    "warning.deep": "#795600",
    "danger": "#c9190b",
    "danger.tint": "#faeae8",
    "danger.deep": "#a30000",

    // These are only used in dark-mode redefines.
    "primary.fallback":       "0066cc",
    "surface.above":          "#26292d",
    "surface.input-fill":     "#36373a",
    "border.field-underline": "#aaabac",
    
});

// Dark theme overrides. Surface values are pinned near PatternFly 4's
// BackgroundColor--100 (#151515) and the drawer surface (#18191a); lighter
// surfaces visibly brighten every PF-backed dark panel.
theme("dark", (ctx) => {
    const c = colors;

    // prettier-ignore
    const darkColors: VPPair[] = [
        
        [c.colorInk, "#e0e0e0"],
        [c.colorInkMuted, "#aaabac"],

        [c.colorInkPinDark, "#e0e0e0"],

        // This annoys me for reasons I cannot articulate clearly.
        [c.colorInkPlaceholder, "#aaabac"],

        [c.colorLink,          "#20a9f8"],
        [c.colorLinkHover,     "#73bcf7"],
        [c.colorLinkVisited,   "#a18fff"],

        [c.colorSurface,       "#1b1d21"],
        [c.colorSurfaceRaised, "#212427"],
        [c.colorSurfaceMuted,  "#0f1214"],


        [c.colorBorder,            "#444548"],
        [c.colorBorderEdge,        "#444548"],
        [c.colorBorderSubtle,      "#57585a"],

        
        [c.colorPrimary,     "#1fa7f8"],
        [c.colorActive,      "#1fa7f8"],

        [c.colorDisabled,          "#57585a"],
        [c.colorDisabledFill,      "#444548"],
        [c.colorDisabledReadonly,  "#aaabac"],

        [c.colorNeutral,     "#a2d9d9"],
        [c.colorNeutralDeep, "#73c5c5"],
        [c.colorSuccess,     "#5ba352"],

        [c.colorSuccessDeep, "#f3faf2"],
        [c.colorInfo,        "#73bcf7"],
        [c.colorInfoDeep,    "#e7f1fa"],

        [c.colorWarning,     "#f0ab00"],
        [c.colorWarningDeep, "#f4c145"],

        [c.colorDanger,      "#fe5142"],
        [c.colorDangerDeep,  "#ff7468"],
    ];

    darkColors.forEach(([v, p]) => ctx.variable(v, oklchTransform(p)));
});
