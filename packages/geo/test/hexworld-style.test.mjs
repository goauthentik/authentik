import assert from "node:assert/strict";
import { test } from "node:test";

import { HEXWORLD_ATTRIBUTION, buildHexworldStyle } from "../out/hexworld/style.js";

const style = buildHexworldStyle({ archiveUrl: "/static/dist/assets/maps/hexworld.pmtiles" });

test("style uses the pmtiles protocol with promoted h3 ids", () => {
    const source = style.sources.hexworld;
    assert.equal(source.type, "vector");
    assert.equal(source.url, "pmtiles:///static/dist/assets/maps/hexworld.pmtiles");
    assert.deepEqual(source.promoteId, { hex: "h3" });
    assert.equal(source.maxzoom, 8);
    assert.equal(source.attribution, HEXWORLD_ATTRIBUTION);
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

test("style has a borders line layer sourced from the borders source-layer", () => {
    const ids = style.layers.map((layer) => layer.id);
    const outlineIdx = ids.indexOf("hexworld-hex-outline");
    const bordersIdx = ids.indexOf("hexworld-borders");
    assert.notEqual(bordersIdx, -1, "expected a hexworld-borders layer");
    assert.ok(bordersIdx > outlineIdx, "borders must render above hex outlines");
    const borders = style.layers[bordersIdx];
    assert.equal(borders.type, "line");
    assert.equal(borders["source-layer"], "borders");
});

test("airgap: default style references no absolute URLs", () => {
    const json = JSON.stringify(style);
    assert.ok(!/https?:\/\//.test(json), "style must not reach external hosts");
});

test("dark theme swaps palette", () => {
    const dark = buildHexworldStyle({ archiveUrl: "/x.pmtiles", theme: "dark" });
    const bg = (id, s) => s.layers.find((l) => l.id === id).paint["background-color"];
    assert.notEqual(bg("hexworld-background", dark), bg("hexworld-background", style));
});
