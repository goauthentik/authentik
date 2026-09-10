import type { Polygon } from "geojson";
import { cellToBoundary } from "h3-js";

/**
 * H3 boundary as a closed GeoJSON polygon ring. Cells crossing the antimeridian are shifted into a
 * continuous 0..360 range so downstream tiling doesn't draw world-spanning slivers.
 */
export function cellPolygon(cell: string): Polygon {
    let ring = cellToBoundary(cell, true);
    const lngs = ring.map(([lng]) => lng);
    if (Math.max(...lngs) - Math.min(...lngs) > 180) {
        ring = ring.map(([lng, lat]) => [lng < 0 ? lng + 360 : lng, lat]);
    }
    const closed = [...ring, ring[0]!];
    return { type: "Polygon", coordinates: [closed] };
}
