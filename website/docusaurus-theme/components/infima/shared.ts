import {
    infimalColors,
    utilityColorDefs,
} from "@goauthentik/docusaurus-theme/components/infima/constants.ts";

import { useCallback, useMemo, useSyncExternalStore } from "react";

export interface Shade {
    name: string;
    suffix: string;
}

export interface ColorGroup {
    name: string;
    cssVar: string;
    shades: Shade[];
}

export interface UtilityColor {
    name: string;
    cssVar: string;
}

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

export function computeColor(cssVar: string): { hex: string | null; contrastColor: string } {
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
    name: string;
    colors: ComputedColor[];
}

export function computePalette(): ComputedColorGroup[] {
    return infimalColors.map((group) => ({
        name: group.name,
        colors: group.shades.map((shade) => {
            const cssVar = `${group.cssVar}${shade.suffix}`;
            const { hex, contrastColor } = computeColor(cssVar);
            return { cssVar, label: shade.name, hex, contrastColor };
        }),
    }));
}

export function computeUtilityColors(): ComputedColor[] {
    return utilityColorDefs.map((color) => {
        const { hex, contrastColor } = computeColor(color.cssVar);
        return { cssVar: color.cssVar, label: color.name, hex, contrastColor };
    });
}

export function useComputedPalette(colorMode: string): Map<string, ComputedColor[]> {
    const subscribe = useCallback((callback: () => void) => {
        const observer = new MutationObserver(callback);
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ["data-theme"],
        });
        return () => observer.disconnect();
    }, []);

    const getSnapshot = useCallback(() => {
        return JSON.stringify({ colorMode, palette: computePalette() });
    }, [colorMode]);

    const getServerSnapshot = useCallback(() => {
        return JSON.stringify({ colorMode, palette: [] });
    }, [colorMode]);

    const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

    return useMemo(() => {
        const parsed = JSON.parse(snapshot) as { colorMode: string; palette: ComputedColorGroup[] };

        const colorMap = new Map<string, ComputedColor[]>();
        for (const group of parsed.palette) {
            colorMap.set(group.name.toLowerCase(), group.colors);
        }

        return colorMap;
    }, [snapshot]);
}

export function useComputedUtilityColors(colorMode: string): ComputedColor[] {
    const subscribe = useCallback((callback: () => void) => {
        const observer = new MutationObserver(callback);
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ["data-theme"],
        });
        return () => observer.disconnect();
    }, []);

    const getSnapshot = useCallback(() => {
        return JSON.stringify({ colorMode, colors: computeUtilityColors() });
    }, [colorMode]);

    const getServerSnapshot = useCallback(() => {
        return JSON.stringify({ colorMode, colors: [] });
    }, [colorMode]);

    const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
    return useMemo(() => JSON.parse(snapshot).colors, [snapshot]);
}
