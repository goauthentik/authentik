import { cellToLatLng } from "h3-js";

import type { FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";

interface CountryEntry {
    code: string;
    // [lngMin, latMin, lngMax, latMax]
    bbox: [number, number, number, number];
    polygons: Position[][][];
}

export interface CountryIndex {
    entries: CountryEntry[];
}

function pickCode(props: Record<string, unknown> | null | undefined): string | null {
    if (!props) return null;
    for (const key of ["ISO_A2", "iso_a2", "ISO_A3", "iso_a3", "ADM0_A3", "adm0_a3"]) {
        const value = props[key];
        if (typeof value === "string" && value.trim() && value !== "-99") return value;
    }
    return null;
}

function ringBBox(ring: Position[]): [number, number, number, number] {
    let lngMin = Infinity;
    let latMin = Infinity;
    let lngMax = -Infinity;
    let latMax = -Infinity;
    for (const [lng, lat] of ring as Array<[number, number]>) {
        if (lng < lngMin) lngMin = lng;
        if (lng > lngMax) lngMax = lng;
        if (lat < latMin) latMin = lat;
        if (lat > latMax) latMax = lat;
    }
    return [lngMin, latMin, lngMax, latMax];
}

function polygonsBBox(polygons: Position[][][]): [number, number, number, number] {
    let lngMin = Infinity;
    let latMin = Infinity;
    let lngMax = -Infinity;
    let latMax = -Infinity;
    for (const rings of polygons) {
        for (const ring of rings) {
            const [xMin, yMin, xMax, yMax] = ringBBox(ring);
            if (xMin < lngMin) lngMin = xMin;
            if (yMin < latMin) latMin = yMin;
            if (xMax > lngMax) lngMax = xMax;
            if (yMax > latMax) latMax = yMax;
        }
    }
    return [lngMin, latMin, lngMax, latMax];
}

/**
 * Build a searchable index of countries from a Natural Earth admin-0
 * FeatureCollection. Each entry keeps the country's ISO code, its
 * pre-computed bounding box (for fast rejection), and its polygon rings.
 * Both Polygon and MultiPolygon geometries are supported; anything else is
 * skipped silently.
 */
export function buildCountryIndex(collection: FeatureCollection): CountryIndex {
    const entries: CountryEntry[] = [];
    for (const feature of collection.features) {
        const code = pickCode(feature.properties as Record<string, unknown> | null);
        if (!code) continue;
        const geometry = feature.geometry;
        let polygons: Position[][][];
        if (geometry.type === "Polygon") {
            polygons = [(geometry as Polygon).coordinates];
        } else if (geometry.type === "MultiPolygon") {
            polygons = (geometry as MultiPolygon).coordinates;
        } else {
            continue;
        }
        entries.push({ code, bbox: polygonsBBox(polygons), polygons });
    }
    return { entries };
}

function pointInRing(lng: number, lat: number, ring: Position[]): boolean {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, yi] = ring[i] as [number, number];
        const [xj, yj] = ring[j] as [number, number];
        // Ray-cast to +x: count edge crossings whose y-interval brackets `lat`.
        if (yi > lat !== yj > lat && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
            inside = !inside;
        }
    }
    return inside;
}

function pointInPolygon(lng: number, lat: number, rings: Position[][]): boolean {
    if (rings.length === 0 || !pointInRing(lng, lat, rings[0]!)) return false;
    for (let i = 1; i < rings.length; i++) {
        if (pointInRing(lng, lat, rings[i]!)) return false;
    }
    return true;
}

/**
 * Assign every H3 cell in `cells` to a country by point-in-polygon on the
 * cell centroid. Cells whose centroid falls in no polygon are omitted from
 * the result — the caller treats them as ocean or antarctic ice.
 */
export function assignCountries(cells: Iterable<string>, index: CountryIndex): Map<string, string> {
    const assigned = new Map<string, string>();
    for (const cell of cells) {
        const [lat, lng] = cellToLatLng(cell);
        for (const entry of index.entries) {
            const [lngMin, latMin, lngMax, latMax] = entry.bbox;
            if (lng < lngMin || lng > lngMax || lat < latMin || lat > latMax) continue;
            let hit = false;
            for (const polygon of entry.polygons) {
                if (pointInPolygon(lng, lat, polygon)) {
                    hit = true;
                    break;
                }
            }
            if (hit) {
                assigned.set(cell, entry.code);
                break;
            }
        }
    }
    return assigned;
}
