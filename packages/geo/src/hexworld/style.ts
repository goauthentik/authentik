import type { EventActionsRecord } from "../shared/events.ts";
import { LABEL_MIN_ZOOM, LABEL_TEXT_SIZE, LabelKinds } from "../shared/labels.ts";
import { type BasemapTheme, buildSky } from "../style.ts";
import { HEX_BANDS, MAX_BAND_ZOOM } from "./bands.ts";

import { EventActions } from "@goauthentik/api/src/models/EventActions.ts";

import type {
    BackgroundLayerSpecification,
    ExpressionSpecification,
    FillLayerSpecification,
    LineLayerSpecification,
    StyleSpecification,
    SymbolLayerSpecification,
} from "maplibre-gl";

// Plain text by design: the airgap test forbids external URLs in the style,
// and an in-app link target makes no sense here. The docs page carries the
// osm.org/copyright link; ODbL text attribution suffices on the map itself.
export const HEXWORLD_ATTRIBUTION = "© OpenStreetMap (labels) · Natural Earth";

export interface HexworldStyleOptions {
    archiveURL: string;
    theme?: BasemapTheme;
    glyphsURL?: string;
    attribution?: string;
    /**
     * Highest zoom at which the archive carries hex and border geometry.
     * Defaults to the last entry in HEX_BANDS, which is what the shipped
     * archive is built from.
     */
    maxzoom?: number;
}

interface Palette {
    background: string;
    hex: string;
    hexOutline: string;
    hexLit: string;
    hexHot: string;
    border: string;
    regionBorder: string;
    text: string;
    textHalo: string;
}

const PALETTES: Record<BasemapTheme, Palette> = {
    light: {
        background: "#dfe7ec",
        hex: "#c6d0d8",
        hexOutline: "#b3bfc9",
        hexLit: "#f0ab00",
        hexHot: "#c9190b",
        border: "#6a7684",
        regionBorder: "#95a1ad",
        text: "#3c4852",
        textHalo: "#f4f7f9",
    },
    dark: {
        background: "#161b22",
        hex: "#2b333d",
        hexOutline: "#39434f",
        hexLit: "#f0ab00",
        hexHot: "#fe5142",
        border: "#8b98a8",
        regionBorder: "#5c6772",
        text: "#aab7c4",
        textHalo: "#10141a",
    },
};

// Aligned with PatternFly chart hues; slightly lifted for the dark basemap.
const WEDGE_COLORS: Record<BasemapTheme, EventActionsRecord> = {
    light: {
        [EventActions.Login]: "#3e8635",
        [EventActions.LoginFailed]: "#c9190b",
        [EventActions.Logout]: "#2b9af3",
        [EventActions.AuthorizeApplication]: "#8476d1",
        [EventActions.UnknownDefaultOpenApi]: "#8a8d90",
    },
    dark: {
        [EventActions.Login]: "#5ba352",
        [EventActions.LoginFailed]: "#fe5142",
        [EventActions.Logout]: "#73bcf7",
        [EventActions.AuthorizeApplication]: "#a18fff",
        [EventActions.UnknownDefaultOpenApi]: "#8a8d90",
    },
};

export function wedgeColors(theme: BasemapTheme = "light"): EventActionsRecord {
    return WEDGE_COLORS[theme];
}

/** Zoom span over which one band fades into the next. */
export const BAND_FADE_WINDOW = 0.9;

/**
 * Data-driven opacity that cross-fades the hex bands instead of letting the
 * grid pop when the tile zoom crosses a band boundary. The archive carries
 * res-3 geometry one tile zoom into the res-4 band (`hex-r3-fade`), so both
 * grids coexist in the fade window; at z7 the res-5 overlay fades in over the
 * res-4 base, which persists (it backs the overlay outside the detail zone).
 * Features without a `res` property (older archives) keep the base opacity.
 */
export function bandFadeOpacity(base: number): ExpressionSpecification {
    const [coarse, mid, detail] = HEX_BANDS;
    const opacity = (r3: number, r4: number, r5: number): ExpressionSpecification => [
        "match",
        ["get", "res"],
        coarse!.res,
        r3,
        mid!.res,
        r4,
        detail!.res,
        r5,
        base,
    ];

    return [
        "interpolate",
        ["linear"],
        ["zoom"],
        mid!.minzoom,
        opacity(base, 0, 0),
        mid!.minzoom + BAND_FADE_WINDOW,
        opacity(0, base, 0),
        detail!.minzoom,
        opacity(0, base, 0),
        detail!.minzoom + BAND_FADE_WINDOW,
        opacity(0, base, base),
    ];
}

const DEFAULT_GLYPHS = "/static/dist/assets/maps/fonts/{fontstack}/{range}.pbf";
const TEXT_FIELD: ExpressionSpecification = ["coalesce", ["get", "name:en"], ["get", "name"]];
const FONT = ["Noto Sans Regular"];

export function buildHexworldStyle(options: HexworldStyleOptions): StyleSpecification {
    const palette = PALETTES[options.theme ?? "light"];
    const eventPaint: ExpressionSpecification = [
        "interpolate",
        ["linear"],
        ["coalesce", ["feature-state", "events"], 0],
        0,
        palette.hex,
        1,
        palette.hexLit,
        25,
        palette.hexHot,
    ];

    const background: BackgroundLayerSpecification = {
        id: "hexworld-background",
        type: "background",
        paint: { "background-color": palette.background },
    };

    const hexFill: FillLayerSpecification = {
        "id": "hexworld-hex",
        "type": "fill",
        "source": "hexworld",
        "source-layer": "hex",
        "paint": { "fill-color": eventPaint, "fill-opacity": bandFadeOpacity(0.95) },
    };

    const hexOutline: LineLayerSpecification = {
        "id": "hexworld-hex-outline",
        "type": "line",
        "source": "hexworld",
        "source-layer": "hex",
        "paint": {
            "line-color": palette.hexOutline,
            "line-width": 0.5,
            "line-opacity": bandFadeOpacity(1),
        },
    };

    const regionBorders: LineLayerSpecification = {
        "id": "hexworld-region-borders",
        "type": "line",
        "source": "hexworld",
        "source-layer": "borders",
        // Res 4 (~52 km cells) starts at z3 with the current bands, so admin-1
        // borders start there too — anything lower turns the continents into
        // a mesh at res 3's ~138 km cells.
        "minzoom": 3,
        "filter": ["==", ["get", "level"], 1],
        "paint": {
            "line-color": palette.regionBorder,
            "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 8, 1.0],
            "line-opacity": bandFadeOpacity(0.7),
        },
    };

    const borders: LineLayerSpecification = {
        "id": "hexworld-borders",
        "type": "line",
        "source": "hexworld",
        "source-layer": "borders",
        "filter": ["==", ["get", "level"], 0],
        // Scaled so borders remain visible at world zoom without turning into
        // slabs when zoomed in — heavier than the hex outline and the region
        // border layer at every stop.
        "paint": {
            "line-color": palette.border,
            "line-width": ["interpolate", ["linear"], ["zoom"], 0, 0.9, 4, 1.4, 8, 2.2],
            "line-opacity": bandFadeOpacity(0.9),
        },
    };

    const labelLayers: SymbolLayerSpecification[] = Array.from(LabelKinds, (kind) => ({
        "id": `hexworld-label-${kind}`,
        "type": "symbol",
        "source": "hexworld",
        "source-layer": "places",
        "minzoom": LABEL_MIN_ZOOM[kind],
        "filter": ["==", ["get", "kind"], kind],
        "layout": {
            "text-field": TEXT_FIELD,
            "text-font": FONT,
            "text-size": LABEL_TEXT_SIZE[kind],
            // Ascending placement order: most populous places claim space
            // first, so China outranks its neighbors instead of losing the
            // collision lottery to whichever label rendered first.
            "symbol-sort-key": ["*", -1, ["coalesce", ["get", "population"], 0]],
        },
        "paint": {
            "text-color": palette.text,
            "text-halo-color": palette.textHalo,
            "text-halo-width": 1.2,
        },
    }));

    return {
        version: 8,
        projection: { type: "globe" },
        sky: buildSky(options.theme ?? "light"),
        glyphs: options.glyphsURL ?? DEFAULT_GLYPHS,
        sources: {
            hexworld: {
                type: "vector",
                url: `pmtiles://${options.archiveURL}`,
                promoteId: { hex: "h3" },
                attribution: options.attribution ?? HEXWORLD_ATTRIBUTION,
                // Derived from HEX_BANDS so it cannot drift from what the
                // archive actually carries. Declaring a higher value makes
                // MapLibre fetch real tiles beyond the last band, which hold
                // only the places layer: land and borders vanish and labels
                // float on empty ocean. Declaring a lower one wastes the
                // finest band entirely, since MapLibre overzooms instead of
                // fetching it.
                maxzoom: options.maxzoom ?? MAX_BAND_ZOOM,
            },
        },
        // Region borders sit under country borders so the country line wins
        // any pixel overlap; both sit above the hex outline and under the labels.
        layers: [background, hexFill, hexOutline, regionBorders, borders, ...labelLayers],
    };
}
