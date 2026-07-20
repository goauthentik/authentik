import { cellsToDirectedEdge, directedEdgeToBoundary, gridDisk } from "h3-js";

import type { Feature, LineString } from "geojson";

const OCEAN_CODE = "";

export interface BorderProperties {
    level: 0 | 1;
    a: string;
    b: string;
    /**
     * H3 cell ids of the two endpoints, sorted so `aCell < bCell` matches
     * the `(a, b)` code ordering. Kept on the in-memory feature for
     * downstream zone filtering; the generator strips them before tippecanoe
     * sees the geojsonl so shipped tiles stay small.
     */
    aCell?: string;
    bCell?: string;
}

export type BorderFeature = Feature<LineString, BorderProperties>;

export interface BorderAssignments {
    country: Map<string, string>;
    /** Optional admin-1 assignment. Region-level borders only emit where both
     *  cells carry a region code, and only where the country codes match. */
    region?: Map<string, string>;
    /**
     * Optional full land-cell set at this resolution. When provided, every
     * land cell whose neighbor is not a land cell gets a level-0 coastal edge
     * against the neighbor. Deduped alongside country-vs-country segments so
     * no cell pair produces two features.
     */
    land?: Set<string>;
}

function pushBorder(
    features: BorderFeature[],
    seen: Set<string>,
    cell: string,
    neighbor: string,
    level: 0 | 1,
    aCode: string,
    bCode: string,
): void {
    const [first, second] = cell < neighbor ? [cell, neighbor] : [neighbor, cell];
    const key = `${first}|${second}`;
    if (seen.has(key)) return;
    seen.add(key);
    const [firstCode, secondCode] = first === cell ? [aCode, bCode] : [bCode, aCode];
    const edge = cellsToDirectedEdge(first, second);
    features.push({
        type: "Feature",
        properties: {
            level,
            a: firstCode,
            b: secondCode,
            aCell: first,
            bCell: second,
        },
        geometry: { type: "LineString", coordinates: directedEdgeToBoundary(edge, true) },
    });
}

/**
 * Extract hex-aligned border segments. Walks every land cell, checks the six
 * neighbors, and emits the shared H3 edge whenever the neighbor differs at
 * the strongest applicable level: country (level 0) first, region (level 1)
 * only when countries match. When `land` is provided, land cells whose
 * neighbor is not a land cell also emit a level-0 coastal edge so every
 * country is fully enclosed against water. Each unordered cell pair produces
 * at most one feature — canonicalized on lexical order of the two cell ids.
 */
export function borderEdges(assignments: BorderAssignments): BorderFeature[] {
    const { country, region, land } = assignments;
    const features: BorderFeature[] = [];
    const seen = new Set<string>();

    // With a land set we walk every land cell (so islands the country
    // point-in-polygon missed still get their perimeter drawn); without it,
    // walk the country-tagged cells only and skip coastal detection.
    const cells: Iterable<string> = land ?? country.keys();

    for (const cell of cells) {
        const cellIsLand = land ? land.has(cell) : country.has(cell);
        if (!cellIsLand) continue;
        const cellCountry = country.get(cell) ?? OCEAN_CODE;
        const cellRegion = region?.get(cell);
        for (const neighbor of gridDisk(cell, 1)) {
            if (neighbor === cell) continue;
            const neighborIsLand = land
                ? land.has(neighbor)
                : country.has(neighbor);
            if (!neighborIsLand) {
                if (land) {
                    pushBorder(features, seen, cell, neighbor, 0, cellCountry, OCEAN_CODE);
                }
                continue;
            }
            const neighborCountry = country.get(neighbor) ?? OCEAN_CODE;
            if (neighborCountry !== cellCountry) {
                pushBorder(features, seen, cell, neighbor, 0, cellCountry, neighborCountry);
                continue;
            }
            if (!region) continue;
            const neighborRegion = region.get(neighbor);
            if (!cellRegion || !neighborRegion || cellRegion === neighborRegion) continue;
            pushBorder(features, seen, cell, neighbor, 1, cellRegion, neighborRegion);
        }
    }
    return features;
}
