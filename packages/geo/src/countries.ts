import type { FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";
import { cellToLatLng } from "h3-js";

interface AdminEntry {
    code: string;
    // [lngMin, latMin, lngMax, latMax]
    bbox: [number, number, number, number];
    polygons: Position[][][];
}

export interface AdminIndex {
    entries: AdminEntry[];
}

export type CountryIndex = AdminIndex;
export type RegionIndex = AdminIndex;

const COUNTRY_CODE_KEYS = ["ISO_A2", "iso_a2", "ISO_A3", "iso_a3", "ADM0_A3", "adm0_a3"];
const REGION_CODE_KEYS = ["iso_3166_2", "ISO_3166_2", "adm1_code", "ADM1_CODE", "code_hasc"];

function pickCode(
    props: Record<string, unknown> | null | undefined,
    keys: readonly string[],
): string | null {
    if (!props) return null;
    for (const key of keys) {
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

function buildIndex(collection: FeatureCollection, codeKeys: readonly string[]): AdminIndex {
    const entries: AdminEntry[] = [];
    for (const feature of collection.features) {
        const code = pickCode(feature.properties as Record<string, unknown> | null, codeKeys);
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

/**
 * Build a searchable index of countries from a Natural Earth admin-0
 * FeatureCollection. Each entry keeps the country's ISO code, its
 * pre-computed bounding box (for fast rejection), and its polygon rings.
 * Both Polygon and MultiPolygon geometries are supported; anything else is
 * skipped silently.
 */
export function buildCountryIndex(collection: FeatureCollection): CountryIndex {
    return buildIndex(collection, COUNTRY_CODE_KEYS);
}

/**
 * Build a searchable index of admin-1 regions (states, provinces) from a
 * Natural Earth admin-1 FeatureCollection. Prefers ISO 3166-2 codes with a
 * fallback to Natural Earth's `adm1_code` or the HASC identifier — the 50m
 * dataset covers only nine countries, so use `ne_10m_admin_1_states_provinces`
 * as input for global coverage.
 */
export function buildRegionIndex(collection: FeatureCollection): RegionIndex {
    return buildIndex(collection, REGION_CODE_KEYS);
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

function assignBy(cells: Iterable<string>, index: AdminIndex): Map<string, string> {
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

/**
 * Assign every H3 cell in `cells` to a country by point-in-polygon on the
 * cell centroid. Cells whose centroid falls in no polygon are omitted from
 * the result — the caller treats them as ocean or antarctic ice.
 */
export function assignCountries(cells: Iterable<string>, index: CountryIndex): Map<string, string> {
    return assignBy(cells, index);
}

/** Like `assignCountries` but returns the admin-1 (state/province) code. */
export function assignRegions(cells: Iterable<string>, index: RegionIndex): Map<string, string> {
    return assignBy(cells, index);
}
