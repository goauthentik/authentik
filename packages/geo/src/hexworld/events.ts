import { bandForZoom } from "./bands.js";

import { latLngToCell } from "h3-js";

export interface GeoPoint {
    lat: number;
    lon: number;
}

/** Aggregate event locations into H3 cells at the active zoom band's resolution. */
export function cellCounts(markers: GeoPoint[], zoom: number): Map<string, number> {
    const { res } = bandForZoom(zoom);
    const counts = new Map<string, number>();
    for (const { lat, lon } of markers) {
        const cell = latLngToCell(lat, lon, res);
        counts.set(cell, (counts.get(cell) ?? 0) + 1);
    }
    return counts;
}
