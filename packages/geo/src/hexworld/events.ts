import { bandForZoom } from "./bands.js";

import { latLngToCell } from "h3-js";

export interface GeoPoint {
    lat: number;
    lon: number;
}

/**
 * Aggregate event locations into H3 cells at the active zoom band's
 * resolution. At z7-8 the archive carries both a res-4 base fill and a res-5
 * overlay in the populated-area zone — we light both, keyed by cell id. The
 * base cell tints hide under the visible overlay inside the zone, and the
 * overlay cells tint the (empty) tiles outside the zone with no visible
 * effect, so the caller doesn't need to know the zone at runtime.
 */
export function cellCounts(markers: GeoPoint[], zoom: number): Map<string, number> {
    const { res } = bandForZoom(zoom);
    const counts = new Map<string, number>();
    const bump = (cell: string) => counts.set(cell, (counts.get(cell) ?? 0) + 1);
    for (const { lat, lon } of markers) {
        bump(latLngToCell(lat, lon, res));
        // At z7-8 the archive carries a res-5 overlay only inside the
        // populated-area zone; outside it, the res-4 base is the visible
        // fill. Light both so events tint whichever hex is on top at each
        // pixel without the client needing to know the zone at runtime.
        if (res === 5) bump(latLngToCell(lat, lon, 4));
    }
    return counts;
}
