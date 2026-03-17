import { ColorMode } from "@docusaurus/theme-common";

export type Shade = [label: string, suffix: string];

export interface ColorGroupProp {
    label: string;
    cssVar: string;
    shades: Shade[];
}

export type ColorEntry = [label: string, cssVar: string];

export const Prefix = {
    Infima: "--ifm-",
    Authentik: "--ak-",
} as const satisfies Record<string, string>;

export interface ComputedColor {
    cssVar: string;
    label: string;
    hex: string | null;
    contrastColor: string;
}

export function getContrastColor(hexColor: string | null): string {
    if (!hexColor || hexColor === "transparent" || hexColor.startsWith("rgba")) {
        return "#000000";
    }
    const hex = hexColor.replace("#", "");
    if (hex.length !== 6) return "#000000";
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? "#1a1a1a" : "#ffffff";
}

export function rgbToHex(rgb: string): string | null {
    if (!rgb || rgb === "transparent") return null;
    if (rgb.startsWith("#")) return rgb;
    const match = rgb.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return null;

    const [, r = "", g = "", b = ""] = match;

    const hex = (x: string): string => parseInt(x, 10).toString(16).padStart(2, "0");
    return `#${hex(r)}${hex(g)}${hex(b)}`;
}

export function computeColor(cssVar: string): Pick<ComputedColor, "hex" | "contrastColor"> {
    if (typeof document === "undefined") {
        return { hex: null, contrastColor: "#000000" };
    }
    const computedColor = getComputedStyle(document.documentElement)
        .getPropertyValue(cssVar)
        .trim();

    const hex = rgbToHex(computedColor) || computedColor || null;
    const contrastColor = getContrastColor(hex);

    return { hex, contrastColor };
}

export interface ComputedColorGroup {
    label: string;
    colors: ComputedColor[];
}

export function createComputedColorGroup(
    group: ColorGroupProp,
    _colorMode: ColorMode,
): ComputedColorGroup {
    return {
        label: group.label,
        colors: group.shades.map(([label, suffix]) => {
            const cssVar = `${Prefix.Infima}${group.cssVar}${suffix}`;
            const { hex, contrastColor } = computeColor(cssVar);

            return { cssVar, label, hex, contrastColor };
        }),
    };
}
