import type { PlaceLabel } from "@goauthentik/geo/shared";

import { cellToChildren, cellToParent, gridDisk, latLngToCell } from "h3-js";

const RES_BASE = 4;
const RES_DETAIL = 5;

export interface DetailZoneOptions {
    /** Ring radius in res-4 cells around each qualifying label. */
    ring: number;
    /** Minimum population for a locality to seed the zone. 0 → all localities. */
    minPop: number;
}

export interface DetailZone {
    /** Res-4 cells that fall inside the detail zone. */
    baseCells: Set<string>;
    /** Res-5 cells intersecting the zone. */
    detailCells: Set<string>;
    /** How many labels contributed to the zone (after minPop filter). */
    seedCount: number;
}

/**
 * Compute the "populated area" detail zone from a set of place labels. Every
 * locality above `minPop` seeds a `gridDisk(ring)` around its containing
 * res-4 cell; the union is the zone. The corresponding res-5 cells are the
 * seven-child expansion of each res-4 zone cell.
 *
 * The zone intentionally sits at res-4 rather than res-5 so mixing math is
 * simple: at z7-8 the archive carries res-4 cells outside the zone as the
 * base fill, and res-5 zone children on top. Both are exact parents of the
 * other in area (7×res-5 = res-4), even though their vertices interlock.
 */
export function computeDetailZone(
    labels: Iterable<PlaceLabel>,
    options: DetailZoneOptions,
): DetailZone {
    const baseCells = new Set<string>();
    let seedCount = 0;

    for (const label of labels) {
        if (label.kind !== "locality") continue;
        if (label.population < options.minPop) continue;

        seedCount += 1;

        const seedCell = latLngToCell(label.lat, label.lng, RES_BASE);

        for (const cell of gridDisk(seedCell, options.ring)) {
            baseCells.add(cell);
        }
    }

    const detailCells = new Set<string>();

    for (const cell of baseCells) {
        for (const child of cellToChildren(cell, RES_DETAIL)) {
            detailCells.add(child);
        }
    }

    return {
        baseCells,
        detailCells,
        seedCount,
    };
}

/**
 * Intersect a set of res-5 land cells with the detail zone. The generator
 * emits only these cells as the res-5 overlay at z7-8; everything else in
 * the world stays covered by the res-4 base underneath.
 */
export function detailCellsForRes5(landRes5: Iterable<string>, zone: DetailZone): Set<string> {
    const out = new Set<string>();
    for (const cell of landRes5) {
        if (zone.detailCells.has(cell)) out.add(cell);
    }
    return out;
}

/** Test whether a res-5 cell falls inside the zone (via its res-4 parent). */
export function isDetailCell(res5Cell: string, zone: DetailZone): boolean {
    return zone.baseCells.has(cellToParent(res5Cell, RES_BASE));
}
