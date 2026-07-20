import { cellsToDirectedEdge, directedEdgeToBoundary, gridDisk } from "h3-js";

import type { Feature, LineString } from "geojson";

export interface BorderFeature extends Feature<LineString> {
    properties: { a: string; b: string };
}

/**
 * Extract inter-country border segments along H3 cell edges. Iterates every
 * assigned cell, walks its six neighbors via `gridDisk`, and emits the shared
 * H3 edge whenever the neighbor carries a different country code. Each edge
 * appears at most once — dedupe canonicalizes on lexical order of the two
 * cells so both sides of a border walk agree on which side emits.
 */
export function borderEdges(cellCountry: Map<string, string>): BorderFeature[] {
    const features: BorderFeature[] = [];
    const seen = new Set<string>();
    for (const [cell, country] of cellCountry) {
        for (const neighbor of gridDisk(cell, 1)) {
            if (neighbor === cell) continue;
            const neighborCountry = cellCountry.get(neighbor);
            if (!neighborCountry || neighborCountry === country) continue;
            const [first, second] = cell < neighbor ? [cell, neighbor] : [neighbor, cell];
            const key = `${first}|${second}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const edge = cellsToDirectedEdge(first, second);
            const coordinates = directedEdgeToBoundary(edge, true);
            const [firstCountry, secondCountry] =
                first === cell ? [country, neighborCountry] : [neighborCountry, country];
            features.push({
                type: "Feature",
                properties: { a: firstCountry, b: secondCountry },
                geometry: { type: "LineString", coordinates },
            });
        }
    }
    return features;
}
