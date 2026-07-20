import { cellPolygon } from "./cells.js";

import { polygonToCellsExperimental } from "h3-js";

import type { Feature, FeatureCollection, Position } from "geojson";

// Web-mercator projection tops out here; anything past this is off-map anyway
// and h3 is happier when it isn't given cells at the poles.
const MERCATOR_MAX_LAT = 85.051129;

// Meridians where full-world polygons get sliced so no slice is wider than
// ~120 deg — comfortably under h3's transmeridian threshold of 180 deg per
// edge. Only used when a ring's lng span exceeds 180.
const SPLIT_MERIDIANS = [-60, 60];

function clampLat(lat: number): number {
    return Math.max(-MERCATOR_MAX_LAT, Math.min(MERCATOR_MAX_LAT, lat));
}

function ringLngSpan(ring: Position[]): number {
    let min = Infinity;
    let max = -Infinity;
    for (const point of ring) {
        const lng = point[0] as number;
        if (lng < min) min = lng;
        if (lng > max) max = lng;
    }
    return max - min;
}

function intersectAtMeridian(a: Position, b: Position, meridian: number): Position {
    const [ax, ay] = a as [number, number];
    const [bx, by] = b as [number, number];
    const t = (meridian - ax) / (bx - ax);
    return [meridian, ay + t * (by - ay)];
}

/**
 * Sutherland–Hodgman clip of a closed ring against a vertical half-plane at
 * `meridian`. `side` = +1 keeps lng >= meridian, -1 keeps lng <= meridian.
 * Callers close the returned ring themselves.
 */
function clipRingAtMeridian(ring: Position[], meridian: number, side: 1 | -1): Position[] {
    const test = (p: Position) => (side === 1 ? p[0]! >= meridian : p[0]! <= meridian);
    // Drop the trailing closing point if present so we don't emit it twice.
    const open =
        ring.length > 1 &&
        ring[0]![0] === ring[ring.length - 1]![0] &&
        ring[0]![1] === ring[ring.length - 1]![1]
            ? ring.slice(0, -1)
            : ring;
    if (open.length === 0) return [];

    const out: Position[] = [];
    for (let i = 0; i < open.length; i++) {
        const cur = open[i]!;
        const prev = open[(i - 1 + open.length) % open.length]!;
        const curIn = test(cur);
        const prevIn = test(prev);
        if (curIn) {
            if (!prevIn) out.push(intersectAtMeridian(prev, cur, meridian));
            out.push(cur);
        } else if (prevIn) {
            out.push(intersectAtMeridian(prev, cur, meridian));
        }
    }
    return out;
}

function closeRing(ring: Position[]): Position[] {
    if (ring.length === 0) return ring;
    const first = ring[0]!;
    const last = ring[ring.length - 1]!;
    if (first[0] === last[0] && first[1] === last[1]) return ring;
    return [...ring, first];
}

/**
 * Preprocess a GeoJSON polygon (outer + holes) into one or more polygons that
 * h3's polygonToCells can handle: latitudes clamped to the web-mercator range,
 * and any ring wider than 180 deg longitude split at SPLIT_MERIDIANS. Even a
 * -180..180 polygon (Antarctica in NE 50m) yields sub-180 slices this way.
 */
function normalizePolygon(polygon: Position[][]): Position[][][] {
    const clamped = polygon.map((ring) =>
        ring.map(([lng, lat]) => [lng, clampLat(lat as number)] as Position),
    );
    if (!clamped.some((ring) => ringLngSpan(ring) > 180)) return [clamped];

    // Slice bands: [-180, -60], [-60, 60], [60, 180].
    const bands: Array<[number, number]> = [
        [-Infinity, SPLIT_MERIDIANS[0]!],
        [SPLIT_MERIDIANS[0]!, SPLIT_MERIDIANS[1]!],
        [SPLIT_MERIDIANS[1]!, Infinity],
    ];
    const result: Position[][][] = [];
    for (const [minLng, maxLng] of bands) {
        const rings: Position[][] = [];
        for (const ring of clamped) {
            let sliced = ring;
            if (Number.isFinite(minLng)) sliced = clipRingAtMeridian(sliced, minLng, 1);
            if (Number.isFinite(maxLng)) sliced = clipRingAtMeridian(sliced, maxLng, -1);
            const closed = closeRing(sliced);
            if (closed.length >= 4) rings.push(closed);
        }
        if (rings.length > 0) result.push(rings);
    }
    return result;
}

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
            for (const normalized of normalizePolygon(polygon)) {
                // polygonToCellsExperimental with containmentCenter matches the
                // legacy polygonToCells behavior but survives polar polygons
                // that the legacy variant refuses (e.g. Antarctica strips).
                for (const cell of polygonToCellsExperimental(
                    normalized,
                    res,
                    "containmentCenter",
                    true,
                )) {
                    cells.add(cell);
                }
            }
        }
    }
    return cells;
}

export function hexFeature(cell: string, country?: string | null): Feature {
    const properties: Record<string, string> = { h3: cell };
    if (country) properties.country = country;
    return {
        type: "Feature",
        properties,
        geometry: cellPolygon(cell),
    };
}
