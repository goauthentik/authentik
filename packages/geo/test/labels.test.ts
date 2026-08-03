import { capLocalities, dedupePlaces, normalizePlace, placeFeature } from "../src/labels.ts";
import { required } from "./helpers.ts";

import { expect, test } from "vitest";

const berlin = {
    "kind": "locality",
    "name": "Berlin",
    "name:en": "Berlin",
    "min_zoom": 4,
    "population": 3600000,
};

test("normalizePlace accepts v4 property names", () => {
    const place = normalizePlace(berlin, 13.405, 52.52);
    expect(place).toStrictEqual({
        kind: "locality",
        name: "Berlin",
        nameEn: "Berlin",
        lng: 13.405,
        lat: 52.52,
        minZoom: 4,
        population: 3600000,
    });
});

test("normalizePlace accepts legacy pmap:-prefixed names", () => {
    const place = required(
        normalizePlace({ "pmap:kind": "country", "name": "France", "pmap:min_zoom": 1 }, 2.2, 46.6),
        "France",
    );
    expect(place.kind).toBe("country");
    // Countries get hexworld's population tiers, not the dump's min_zoom;
    // with no population recorded, the label waits for z3.
    expect(place.minZoom).toBe(3);
    expect(place.population).toBe(0);
});

test("normalizePlace rejects unwanted kinds and nameless places", () => {
    // spellchecker:disable-next-line
    expect(normalizePlace({ kind: "neighbourhood", name: "Mitte" }, 0, 0)).toBe(null);
    expect(normalizePlace({ kind: "locality" }, 0, 0)).toBe(null);
});

test("dedupePlaces keeps one entry per kind+name+cell, lowest minZoom wins", () => {
    const a = required(normalizePlace(berlin, 13.405, 52.52), "Berlin");
    const b = required(normalizePlace({ ...berlin, min_zoom: 7 }, 13.406, 52.521), "Berlin dup");
    const deduped = dedupePlaces([b, a]);
    expect(deduped.length).toBe(1);
    expect(required(deduped[0], "deduped place").minZoom).toBe(4);
});

test("capLocalities keeps countries/regions and the most populous localities", () => {
    const places = [
        required(normalizePlace({ kind: "country", name: "France", min_zoom: 1 }, 2, 46), "France"),
        required(
            normalizePlace({ kind: "locality", name: "Big", min_zoom: 4, population: 9e6 }, 10, 10),
            "Big",
        ),
        required(
            normalizePlace(
                { kind: "locality", name: "Small", min_zoom: 8, population: 100 },
                20,
                20,
            ),
            "Small",
        ),
    ];
    const capped = capLocalities(places, 1);
    expect(capped.map((p) => p.name).sort()).toStrictEqual(["Big", "France"]);
});

test("placeFeature emits tippecanoe minzoom", () => {
    const feature = placeFeature(required(normalizePlace(berlin, 13.405, 52.52), "Berlin"));
    expect(feature.tippecanoe.minzoom).toBe(4);
    expect(feature.properties.kind).toBe("locality");
    expect(feature.geometry.coordinates).toStrictEqual([13.405, 52.52]);
});

test("country reveal zoom is tiered by population, not the dump's min_zoom", () => {
    // Protomaps assigns e.g. China min_zoom 6 — tuned for their dense basemap.
    // On hexworld, big countries must label from the world view.
    const china = required(
        normalizePlace(
            {
                "kind": "country",
                "name": "中国",
                "name:en": "China",
                "min_zoom": 6,
                "population": 1300000000,
            },
            104,
            35,
        ),
        "China",
    );
    expect(china.minZoom).toBe(0);
    const austria = required(
        normalizePlace(
            {
                "kind": "country",
                // spellchecker:disable-next-line
                "name": "Österreich",
                "name:en": "Austria",
                "min_zoom": 4,
                "population": 8900000,
            },
            14,
            47.5,
        ),
        "Austria",
    );
    expect(austria.minZoom).toBe(2);
    const nauru = required(
        normalizePlace(
            { kind: "country", name: "Nauru", min_zoom: 6, population: 10000 },
            166.9,
            -0.5,
        ),
        "Nauru",
    );
    expect(nauru.minZoom).toBe(3);
});

test("regions reveal uniformly at z3 regardless of the dump's min_zoom", () => {
    const bavaria = required(
        normalizePlace(
            { kind: "region", name: "Bayern", min_zoom: 7, population: 13000000 },
            11.5,
            48.8,
        ),
        "Bavaria",
    );
    expect(bavaria.minZoom).toBe(3);
});
