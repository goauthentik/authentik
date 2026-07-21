import { bandForZoom } from "./bands.ts";

import { cellToBoundary, cellToLatLng, getHexagonEdgeLengthAvg, latLngToCell, UNITS } from "h3-js";

export interface EventPoint {
    lat: number;
    lon: number;
    action?: string;
}

export interface CellBin {
    counts: Map<string, number>;
    total: number;
}

export const OTHER_ACTION = "other";

/** Aggregate event points into H3 cells at the active zoom band's resolution. */
export function binEvents(points: EventPoint[], zoom: number): Map<string, CellBin> {
    const { res } = bandForZoom(zoom);
    const bins = new Map<string, CellBin>();
    for (const point of points) {
        const cell = latLngToCell(point.lat, point.lon, res);
        const action = point.action ?? OTHER_ACTION;
        let bin = bins.get(cell);
        if (!bin) {
            bin = { counts: new Map(), total: 0 };
            bins.set(cell, bin);
        }
        bin.counts.set(action, (bin.counts.get(action) ?? 0) + 1);
        bin.total += 1;
    }
    return bins;
}

/** Points that fall into `cell` when binned at the zoom band's resolution. */
export function pointsInCell<T extends EventPoint>(points: T[], zoom: number, cell: string): T[] {
    const { res } = bandForZoom(zoom);
    return points.filter((point) => latLngToCell(point.lat, point.lon, res) === cell);
}

/**
 * The cell containing a location at the zoom band's resolution, and the
 * points binned into it (empty when the cell holds no events).
 */
export function binAtLocation<T extends EventPoint>(
    points: T[],
    zoom: number,
    lat: number,
    lon: number,
): { cell: string; points: T[] } {
    const cell = latLngToCell(lat, lon, bandForZoom(zoom).res);
    return { cell, points: pointsInCell(points, zoom, cell) };
}

export const MAX_HEIGHT_EDGE_FACTOR = 1.5;
export const MIN_HEIGHT_FRACTION = 0.15;

export interface EventFeatureProperties {
    cell: string;
    action: string;
    count: number;
    total: number;
    height: number;
}

type Position = [number, number]; // [lng, lat]

export interface EventFeature {
    type: "Feature";
    geometry: { type: "Polygon"; coordinates: Position[][] };
    properties: EventFeatureProperties;
}

export interface EventFeatureCollection {
    type: "FeatureCollection";
    features: EventFeature[];
}

const TAU = Math.PI * 2;

/** Local planar frame around a cell center; x east, y north, in degrees-ish. */
function toLocal(centerLat: number, centerLng: number, lat: number, lng: number): Position {
    return [(lng - centerLng) * Math.cos((centerLat * Math.PI) / 180), lat - centerLat];
}

function fromLocal(centerLat: number, centerLng: number, x: number, y: number): Position {
    return [centerLng + x / Math.cos((centerLat * Math.PI) / 180), centerLat + y];
}

/** Bearing 0 = north, increasing clockwise, in [0, TAU). */
function bearingOf(x: number, y: number): number {
    const b = Math.atan2(x, y);
    return b < 0 ? b + TAU : b;
}

/**
 * Intersection of the ray from the origin at `bearing` with the convex
 * perimeter (local coords). The center is inside, so exactly one edge hits.
 */
function perimeterPoint(verts: Position[], bearing: number): Position {
    const dx = Math.sin(bearing);
    const dy = Math.cos(bearing);
    for (let i = 0; i < verts.length; i++) {
        const [x1, y1] = verts[i]!;
        const [x2, y2] = verts[(i + 1) % verts.length]!;
        const ex = x2 - x1;
        const ey = y2 - y1;
        const denominator = dx * ey - dy * ex;
        if (Math.abs(denominator) < 1e-12) continue;
        const t = (x1 * ey - y1 * ex) / denominator;
        const s = (x1 * dy - y1 * dx) / denominator;
        if (t > 0 && s >= -1e-9 && s <= 1 + 1e-9) {
            return [x1 + s * ex, y1 + s * ey];
        }
    }
    // Numerically degenerate; fall back to the first vertex.
    return verts[0]!;
}

/** Clockwise angular distance from `from` to `to` in (0, TAU]. */
function clockwiseDelta(from: number, to: number): number {
    const d = (to - from) % TAU;
    return d <= 0 ? d + TAU : d;
}

function wedgeRing(
    centerLat: number,
    centerLng: number,
    verts: Position[],
    startBearing: number,
    endBearing: number,
): Position[][] {
    const sweep = clockwiseDelta(startBearing, endBearing);
    const points: Position[] = [perimeterPoint(verts, startBearing)];
    const between = verts
        .map((v) => ({ v, delta: clockwiseDelta(startBearing, bearingOf(v[0], v[1])) }))
        .filter(({ delta }) => delta > 1e-9 && delta < sweep - 1e-9)
        .sort((a, b) => a.delta - b.delta);
    for (const { v } of between) points.push(v);
    points.push(perimeterPoint(verts, endBearing % TAU));
    const ring: Position[] = [
        fromLocal(centerLat, centerLng, 0, 0),
        ...points.map(([x, y]) => fromLocal(centerLat, centerLng, x, y)),
    ];
    ring.push(ring[0]!);
    return [ring];
}

function wholeHexRing(boundary: [number, number][]): Position[][] {
    const ring: Position[] = boundary.map(([lat, lng]) => [lng, lat]);
    ring.push(ring[0]!);
    return [ring];
}

export function buildEventFeatures(points: EventPoint[], zoom: number): EventFeatureCollection {
    const bins = binEvents(points, zoom);
    const features: EventFeature[] = [];
    if (bins.size === 0) return { type: "FeatureCollection", features };

    const { res } = bandForZoom(zoom);
    const hMax = MAX_HEIGHT_EDGE_FACTOR * getHexagonEdgeLengthAvg(res, UNITS.m);
    const maxTotal = Math.max(...[...bins.values()].map((bin) => bin.total));

    for (const [cell, bin] of bins) {
        const height = hMax * Math.max(MIN_HEIGHT_FRACTION, bin.total / maxTotal);
        const boundary = cellToBoundary(cell);
        const actions = [...bin.counts.entries()].sort((a, b) => b[1] - a[1]);

        if (actions.length === 1) {
            const [action, count] = actions[0]!;
            features.push({
                type: "Feature",
                geometry: { type: "Polygon", coordinates: wholeHexRing(boundary) },
                properties: { cell, action, count, total: bin.total, height },
            });
            continue;
        }

        const [centerLat, centerLng] = cellToLatLng(cell);
        const verts = boundary.map(([lat, lng]) => toLocal(centerLat, centerLng, lat, lng));
        // Largest wedge starts at north; sweep clockwise in descending order.
        let cursor = 0;
        for (const [action, count] of actions) {
            const sweep = (count / bin.total) * TAU;
            features.push({
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: wedgeRing(centerLat, centerLng, verts, cursor, cursor + sweep),
                },
                properties: { cell, action, count, total: bin.total, height },
            });
            cursor += sweep;
        }
    }
    return { type: "FeatureCollection", features };
}
