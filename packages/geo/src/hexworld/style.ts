import { type BasemapTheme, buildSky } from "../style.js";

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
    archiveUrl: string;
    theme?: BasemapTheme;
    glyphsUrl?: string;
    attribution?: string;
}

interface Palette {
    background: string;
    hex: string;
    hexOutline: string;
    hexLit: string;
    hexHot: string;
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
        text: "#3c4852",
        textHalo: "#f4f7f9",
    },
    dark: {
        background: "#161b22",
        hex: "#2b333d",
        hexOutline: "#39434f",
        hexLit: "#f0ab00",
        hexHot: "#fe5142",
        text: "#aab7c4",
        textHalo: "#10141a",
    },
};

const DEFAULT_GLYPHS = "/static/dist/assets/maps/fonts/{fontstack}/{range}.pbf";
const TEXT_FIELD: ExpressionSpecification = [
    "coalesce",
    ["get", "name:en"],
    ["get", "name"],
];
const FONT = ["Noto Sans Regular"];

const LABEL_KINDS = ["country", "region", "locality"] as const;
const LABEL_MIN_ZOOM: Record<(typeof LABEL_KINDS)[number], number> = {
    country: 0,
    region: 4,
    locality: 6,
};
const LABEL_TEXT_SIZE: Record<(typeof LABEL_KINDS)[number], number> = {
    country: 16,
    region: 13,
    locality: 11,
};

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
        id: "hexworld-hex",
        type: "fill",
        source: "hexworld",
        "source-layer": "hex",
        paint: { "fill-color": eventPaint, "fill-opacity": 0.95 },
    };

    const hexOutline: LineLayerSpecification = {
        id: "hexworld-hex-outline",
        type: "line",
        source: "hexworld",
        "source-layer": "hex",
        paint: { "line-color": palette.hexOutline, "line-width": 0.5 },
    };

    const labelLayers: SymbolLayerSpecification[] = LABEL_KINDS.map((kind) => ({
        id: `hexworld-label-${kind}`,
        type: "symbol",
        source: "hexworld",
        "source-layer": "places",
        minzoom: LABEL_MIN_ZOOM[kind],
        filter: ["==", ["get", "kind"], kind],
        layout: {
            "text-field": TEXT_FIELD,
            "text-font": FONT,
            "text-size": LABEL_TEXT_SIZE[kind],
        },
        paint: {
            "text-color": palette.text,
            "text-halo-color": palette.textHalo,
            "text-halo-width": 1.2,
        },
    }));

    return {
        version: 8,
        projection: { type: "globe" },
        sky: buildSky(options.theme ?? "light"),
        glyphs: options.glyphsUrl ?? DEFAULT_GLYPHS,
        sources: {
            hexworld: {
                type: "vector",
                url: `pmtiles://${options.archiveUrl}`,
                promoteId: { hex: "h3" },
                attribution: options.attribution ?? HEXWORLD_ATTRIBUTION,
                maxzoom: 8,
            },
        },
        layers: [background, hexFill, hexOutline, ...labelLayers],
    };
}
