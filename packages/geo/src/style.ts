import { DARK, type Flavor, LIGHT, layers, namedFlavor } from "@protomaps/basemaps";
import type { StyleSpecification } from "maplibre-gl";

export type BasemapTheme = "light" | "dark";

export interface BuildStyleOptions {
    tileUrl: string;
    theme?: BasemapTheme;
    flavor?: Flavor;
    glyphsUrl?: string;
    spriteUrl?: string;
    lang?: string;
    attribution?: string;
    sourceName?: string;
}

const DEFAULT_GLYPHS =
    "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf";

const DEFAULT_ATTRIBUTION =
    '<a href="https://protomaps.com" target="_blank" rel="noopener">Protomaps</a> | ' +
    '<a href="https://openstreetmap.org/copyright" target="_blank" rel="noopener">' +
    "© OpenStreetMap</a>";

export function flavorForTheme(theme: BasemapTheme): Flavor {
    return theme === "dark" ? DARK : LIGHT;
}

export function resolveTileUrl(template: string): string {
    if (/^https?:\/\//i.test(template)) {
        return template;
    }
    if (typeof window !== "undefined" && window.location) {
        return new URL(template, window.location.href).toString();
    }
    return template;
}

export function buildBasemapStyle(options: BuildStyleOptions): StyleSpecification {
    const sourceName = options.sourceName ?? "protomaps";
    const flavor = options.flavor ?? flavorForTheme(options.theme ?? "light");

    const style: StyleSpecification = {
        version: 8,
        glyphs: options.glyphsUrl ?? DEFAULT_GLYPHS,
        sources: {
            [sourceName]: {
                type: "vector",
                tiles: [resolveTileUrl(options.tileUrl)],
                attribution: options.attribution ?? DEFAULT_ATTRIBUTION,
                maxzoom: 14,
            },
        },
        layers: layers(sourceName, flavor, { lang: options.lang ?? "en" }),
    };

    if (options.spriteUrl) {
        style.sprite = options.spriteUrl;
    }

    return style;
}

export { DARK, LIGHT, layers, namedFlavor, type Flavor };
