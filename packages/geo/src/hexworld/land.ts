import { cellPolygon } from "./cells.js";

import { polygonToCells } from "h3-js";

import type { Feature, FeatureCollection } from "geojson";

export function landCells(land: FeatureCollection, res: number): Set<string> {
    const cells = new Set<string>();
    for (const feature of land.features) {
        const geometry = feature.geometry;
        const polygons =
            geometry.type === "Polygon"
                ? [geometry.coordinates]
                : geometry.type === "MultiPolygon"
                  ? geometry.coordinates
                  : [];
        for (const polygon of polygons) {
            for (const cell of polygonToCells(polygon, res, true)) {
                cells.add(cell);
            }
        }
    }
    return cells;
}

export function hexFeature(cell: string): Feature {
    return {
        type: "Feature",
        properties: { h3: cell },
        geometry: cellPolygon(cell),
    };
}
