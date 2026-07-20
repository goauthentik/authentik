import assert from "node:assert/strict";
import { test } from "node:test";

import { buildHexworldStyle, HEXWORLD_ATTRIBUTION } from "../out/hexworld/style.js";

const style = buildHexworldStyle({ archiveURL: "/static/dist/assets/maps/hexworld.pmtiles" });

test("style uses the pmtiles protocol with promoted h3 ids", () => {
    const source = style.sources.hexworld;
    assert.equal(source.type, "vector");
    assert.equal(source.url, "pmtiles:///static/dist/assets/maps/hexworld.pmtiles");
    assert.deepEqual(source.promoteId, { hex: "h3" });
    // The shipped res 3+4 archive carries hex/border geometry only to z6.
    // Declaring a higher source maxzoom makes MapLibre fetch real z7/z8 tiles
    // that contain only the places layer, dropping land and borders.
    assert.equal(source.maxzoom, 6);
    assert.equal(source.attribution, HEXWORLD_ATTRIBUTION);
});

test("source maxzoom is overridable for a finer archive cut", () => {
    const r5 = buildHexworldStyle({ archiveURL: "/x.pmtiles", maxzoom: 8 });
    assert.equal(r5.sources.hexworld.maxzoom, 8);
});

test("style has hex fill + label layers with name:en fallback", () => {
    const ids = style.layers.map((layer) => layer.id);
    assert.ok(ids.includes("hexworld-background"));
    assert.ok(ids.includes("hexworld-hex"));
    const labels = style.layers.filter((layer) => layer.type === "symbol");
    assert.ok(labels.length >= 2, "expected kind-gated symbol layers");
    for (const layer of labels) {
        assert.deepEqual(layer.layout["text-field"], [
            "coalesce",
            ["get", "name:en"],
            ["get", "name"],
        ]);
    }
});

test("style has country + region border layers filtered by level", () => {
    const ids = style.layers.map((layer) => layer.id);
    const outlineIdx = ids.indexOf("hexworld-hex-outline");
    const regionIdx = ids.indexOf("hexworld-region-borders");
    const bordersIdx = ids.indexOf("hexworld-borders");
    assert.notEqual(regionIdx, -1, "expected a hexworld-region-borders layer");
    assert.notEqual(bordersIdx, -1, "expected a hexworld-borders layer");
    assert.ok(regionIdx > outlineIdx, "region borders must render above hex outlines");
    assert.ok(bordersIdx > regionIdx, "country borders must render above region borders");
    const region = style.layers[regionIdx];
    const country = style.layers[bordersIdx];
    assert.equal(region["source-layer"], "borders");
    assert.equal(country["source-layer"], "borders");
    assert.deepEqual(region.filter, ["==", ["get", "level"], 1]);
    assert.deepEqual(country.filter, ["==", ["get", "level"], 0]);
    // Region borders are gated to res-4-and-finer zooms so world view stays
    // readable — res 4 starts at z3 with the current bands.
    assert.ok((region.minzoom ?? 0) >= 3);
});

test("airgap: default style references no absolute URLs", () => {
    const json = JSON.stringify(style);
    assert.ok(!/https?:\/\//.test(json), "style must not reach external hosts");
});

test("dark theme swaps palette", () => {
    const dark = buildHexworldStyle({ archiveURL: "/x.pmtiles", theme: "dark" });
    const bg = (id, s) => s.layers.find((l) => l.id === id).paint["background-color"];
    assert.notEqual(bg("hexworld-background", dark), bg("hexworld-background", style));
});
