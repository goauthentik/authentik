import { latLngToCell } from "h3-js";

import type { Feature } from "geojson";

const KINDS = new Set(["country", "region", "locality"] as const);

export interface PlaceLabel {
    kind: "country" | "region" | "locality";
    name: string;
    nameEn: string | null;
    lng: number;
    lat: number;
    minZoom: number;
    population: number;
}

function pick(props: Record<string, unknown>, ...keys: string[]): unknown {
    for (const key of keys) {
        if (props[key] !== undefined && props[key] !== null) return props[key];
    }
    return undefined;
}

export function normalizePlace(
    props: Record<string, unknown>,
    lng: number,
    lat: number,
): PlaceLabel | null {
    const kind = pick(props, "kind", "pmap:kind");
    const name = pick(props, "name");
    if (typeof kind !== "string" || !KINDS.has(kind as PlaceLabel["kind"])) return null;
    if (typeof name !== "string" || !name.trim()) return null;
    return {
        kind: kind as PlaceLabel["kind"],
        name,
        nameEn: typeof props["name:en"] === "string" ? (props["name:en"] as string) : null,
        lng,
        lat,
        minZoom: Number(pick(props, "min_zoom", "pmap:min_zoom") ?? 8),
        population: Number(pick(props, "population", "pmap:population") ?? 0),
    };
}

/**
 * The same place repeats in every tile from its min_zoom to z8; collapse to one point per
 * kind+name within a res-5 cell, keeping the earliest minZoom.
 */
export function dedupePlaces(places: PlaceLabel[]): PlaceLabel[] {
    const byKey = new Map<string, PlaceLabel>();
    for (const place of places) {
        const key = `${place.kind}:${place.nameEn ?? place.name}:${latLngToCell(place.lat, place.lng, 5)}`;
        const existing = byKey.get(key);
        if (!existing || place.minZoom < existing.minZoom) byKey.set(key, place);
    }
    return [...byKey.values()];
}

export function capLocalities(places: PlaceLabel[], cap: number): PlaceLabel[] {
    const keep = places.filter((p) => p.kind !== "locality");
    const localities = places
        .filter((p) => p.kind === "locality")
        .sort((a, b) => b.population - a.population || a.minZoom - b.minZoom)
        .slice(0, cap);
    return [...keep, ...localities];
}

export interface TippecanoeFeature extends Feature {
    tippecanoe: { minzoom: number };
}

export function placeFeature(place: PlaceLabel): TippecanoeFeature {
    return {
        type: "Feature",
        tippecanoe: { minzoom: Math.max(0, Math.min(8, Math.round(place.minZoom))) },
        properties: {
            kind: place.kind,
            name: place.name,
            "name:en": place.nameEn ?? place.name,
            population: place.population,
        },
        geometry: { type: "Point", coordinates: [place.lng, place.lat] },
    };
}
