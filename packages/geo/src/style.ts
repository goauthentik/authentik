import { DARK, type Flavor, layers, LIGHT, namedFlavor } from "@protomaps/basemaps";
import type { StyleSpecification } from "maplibre-gl";

export type BasemapTheme = "light" | "dark";

/** Named Protomaps flavors usable directly as `flavor`. */
export type FlavorName = "light" | "dark" | "grayscale" | "black";

export interface BuildStyleOptions {
    /**
     * URL of a single PMTiles archive (preferred). May be absolute or
     * root-relative; the `pmtiles://` protocol is added automatically.
     */
    pmtilesUrl?: string;
    /**
     * Legacy XYZ tile template (e.g. served by a tile server). Used only when
     * `pmtilesUrl` is not given.
     */
    tileUrl?: string;
    theme?: BasemapTheme;
    /** A Protomaps `Flavor`, or one of the named flavors. Overrides `theme`. */
    flavor?: Flavor | FlavorName;
    glyphsUrl?: string;
    spriteUrl?: string;
    lang?: string;
    attribution?: string;
    sourceName?: string;
    /** Max zoom of the source archive. The bundled basemap is z7. */
    maxzoom?: number;
}

const DEFAULT_GLYPHS = "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf";

// Roads/places/boundaries are OpenStreetMap-derived (ODbL); the coastline is
// public-domain Natural Earth. OSM attribution is required.
const DEFAULT_ATTRIBUTION =
    '<a href="https://openstreetmap.org/copyright" target="_blank" rel="noopener">' +
    "© OpenStreetMap</a>, <a href=\"https://www.naturalearthdata.com\" " +
    'target="_blank" rel="noopener">Natural Earth</a>';

export function flavorForTheme(theme: BasemapTheme): Flavor {
    return theme === "dark" ? DARK : LIGHT;
}

function resolveFlavor(options: BuildStyleOptions): Flavor {
    const { flavor } = options;
    if (!flavor) return flavorForTheme(options.theme ?? "light");
    return typeof flavor === "string" ? namedFlavor(flavor) : flavor;
}

/** Resolve a possibly-relative URL against the current document origin. */
export function resolveTileUrl(template: string): string {
    if (/^https?:\/\//i.test(template)) return template;
    if (typeof window !== "undefined" && window.location) {
        return new URL(template, window.location.href).toString();
    }
    return template;
}

export function buildBasemapStyle(options: BuildStyleOptions): StyleSpecification {
    const sourceName = options.sourceName ?? "protomaps";
    const flavor = resolveFlavor(options);
    const attribution = options.attribution ?? DEFAULT_ATTRIBUTION;

    let source: StyleSpecification["sources"][string];

    if (options.pmtilesUrl) {
        // A single PMTiles archive served as a static file. The pmtiles
        // protocol supplies the TileJSON (incl. the archive's max zoom).
        source = {
            type: "vector",
            url: `pmtiles://${resolveTileUrl(options.pmtilesUrl)}`,
            attribution,
        };
    } else if (options.tileUrl) {
        source = {
            type: "vector",
            tiles: [resolveTileUrl(options.tileUrl)],
            attribution,
            maxzoom: options.maxzoom ?? 7,
        };
    } else {
        throw new Error("buildBasemapStyle requires either pmtilesUrl or tileUrl");
    }

    const style: StyleSpecification = {
        version: 8,
        glyphs: options.glyphsUrl ?? DEFAULT_GLYPHS,
        sources: { [sourceName]: source },
        layers: layers(sourceName, flavor, { lang: options.lang ?? "en" }),
    };

    if (options.spriteUrl) {
        style.sprite = options.spriteUrl;
    }

    return style;
}

export { DARK, type Flavor, layers, LIGHT, namedFlavor };
