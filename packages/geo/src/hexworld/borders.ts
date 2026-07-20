import { cellsToDirectedEdge, directedEdgeToBoundary, gridDisk } from "h3-js";

import type { Feature, LineString } from "geojson";

export interface BorderProperties {
    level: 0 | 1;
    a: string;
    b: string;
}

export type BorderFeature = Feature<LineString, BorderProperties>;

export interface BorderAssignments {
    country: Map<string, string>;
    /** Optional admin-1 assignment. Region-level borders only emit where both
     *  cells carry a region code, and only where the country codes match. */
    region?: Map<string, string>;
}

/**
 * Extract hex-aligned border segments. Walks every assigned cell, checks the
 * six neighbors, and emits the shared H3 edge whenever the neighbor differs
 * at the strongest applicable level: country (level 0) first, region (level 1)
 * only when countries match. Each unordered cell pair produces at most one
 * feature — canonicalized on lexical order of the two cell ids.
 */
export function borderEdges(assignments: BorderAssignments): BorderFeature[] {
    const { country, region } = assignments;
    const features: BorderFeature[] = [];
    const seen = new Set<string>();
    for (const [cell, cellCountry] of country) {
        const cellRegion = region?.get(cell);
        for (const neighbor of gridDisk(cell, 1)) {
            if (neighbor === cell) continue;
            const neighborCountry = country.get(neighbor);
            if (!neighborCountry) continue;

            let level: 0 | 1;
            let a: string;
            let b: string;
            if (neighborCountry !== cellCountry) {
                level = 0;
                a = cellCountry;
                b = neighborCountry;
            } else if (region) {
                const neighborRegion = region.get(neighbor);
                if (!cellRegion || !neighborRegion || cellRegion === neighborRegion) continue;
                level = 1;
                a = cellRegion;
                b = neighborRegion;
            } else {
                continue;
            }

            const [first, second] = cell < neighbor ? [cell, neighbor] : [neighbor, cell];
            const key = `${first}|${second}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const [firstCode, secondCode] = first === cell ? [a, b] : [b, a];
            const edge = cellsToDirectedEdge(first, second);
            features.push({
                type: "Feature",
                properties: { level, a: firstCode, b: secondCode },
                geometry: { type: "LineString", coordinates: directedEdgeToBoundary(edge, true) },
            });
        }
    }
    return features;
}
