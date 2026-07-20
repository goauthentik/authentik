import assert from "node:assert/strict";
import { test } from "node:test";

import { capLocalities, dedupePlaces, normalizePlace, placeFeature } from "../out/hexworld/labels.js";

const berlin = {
    kind: "locality",
    name: "Berlin",
    "name:en": "Berlin",
    min_zoom: 4,
    population: 3600000,
};

test("normalizePlace accepts v4 property names", () => {
    const place = normalizePlace(berlin, 13.405, 52.52);
    assert.deepEqual(place, {
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
    const place = normalizePlace(
        { "pmap:kind": "country", name: "France", "pmap:min_zoom": 1 },
        2.2,
        46.6,
    );
    assert.equal(place.kind, "country");
    assert.equal(place.minZoom, 1);
    assert.equal(place.population, 0);
});

test("normalizePlace rejects unwanted kinds and nameless places", () => {
    assert.equal(normalizePlace({ kind: "neighbourhood", name: "Mitte" }, 0, 0), null);
    assert.equal(normalizePlace({ kind: "locality" }, 0, 0), null);
});

test("dedupePlaces keeps one entry per kind+name+cell, lowest minZoom wins", () => {
    const a = normalizePlace(berlin, 13.405, 52.52);
    const b = normalizePlace({ ...berlin, min_zoom: 7 }, 13.406, 52.521);
    const deduped = dedupePlaces([b, a]);
    assert.equal(deduped.length, 1);
    assert.equal(deduped[0].minZoom, 4);
});

test("capLocalities keeps countries/regions and the most populous localities", () => {
    const places = [
        normalizePlace({ kind: "country", name: "France", min_zoom: 1 }, 2, 46),
        normalizePlace({ kind: "locality", name: "Big", min_zoom: 4, population: 9e6 }, 10, 10),
        normalizePlace({ kind: "locality", name: "Small", min_zoom: 8, population: 100 }, 20, 20),
    ];
    const capped = capLocalities(places, 1);
    assert.deepEqual(capped.map((p) => p.name).sort(), ["Big", "France"]);
});

test("placeFeature emits tippecanoe minzoom", () => {
    const feature = placeFeature(normalizePlace(berlin, 13.405, 52.52));
    assert.equal(feature.tippecanoe.minzoom, 4);
    assert.equal(feature.properties.kind, "locality");
    assert.deepEqual(feature.geometry.coordinates, [13.405, 52.52]);
});
