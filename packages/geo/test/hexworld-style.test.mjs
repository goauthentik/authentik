import assert from "node:assert/strict";
import { test } from "node:test";

import { buildHexworldStyle, HEXWORLD_ATTRIBUTION } from "../out/hexworld/style.js";

const style = buildHexworldStyle({ archiveURL: "/static/dist/assets/maps/hexworld.pmtiles" });

test("style uses the pmtiles protocol with promoted h3 ids", () => {
    const source = style.sources.hexworld;
    assert.equal(source.type, "vector");
    assert.equal(source.url, "pmtiles:///static/dist/assets/maps/hexworld.pmtiles");
    assert.deepEqual(source.promoteId, { hex: "h3" });
    // The shipped archive carries hex/border geometry through z7 (the zoned
    // res-5 detail band). Declaring higher makes MapLibre fetch z8 tiles
    // that hold only labels; declaring lower wastes the detail band.
    assert.equal(source.maxzoom, 7);
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

test("wedge palette covers the five event actions in both themes", async () => {
    const { wedgeColors } = await import("../out/hexworld/style.js");
    // "11184809" is EventActions.UnknownDefaultOpenApi — drf-spectacular's
    // sentinel for values outside the enum.
    const actions = ["login", "login_failed", "logout", "authorize_application", "11184809"];
    for (const theme of ["light", "dark"]) {
        const colors = wedgeColors(theme);
        for (const action of actions) {
            assert.match(colors[action], /^#[0-9a-f]{6}$/i, `${theme}/${action}`);
        }
    }
});

test("bandFadeOpacity cross-fades bands at their boundaries", async () => {
    const { bandFadeOpacity } = await import("../out/hexworld/style.js");
    const expr = bandFadeOpacity(0.95);
    assert.equal(expr[0], "interpolate");
    assert.deepEqual(expr[2], ["zoom"]);
    // Stops come in [zoom, matchExpression] pairs from index 3 on.
    const stops = [];
    for (let i = 3; i < expr.length; i += 2) stops.push([expr[i], expr[i + 1]]);
    const valueFor = (match, res) => {
        // ["match", ["get","res"], r1, v1, r2, v2, ..., fallback]
        for (let i = 2; i < match.length - 1; i += 2) {
            if (match[i] === res) return match[i + 1];
        }
        return match[match.length - 1];
    };
    const atZoom = (z) => stops.find(([stop]) => stop === z)?.[1];
    // z3: res-3 grid still fully present, res-4 not yet visible.
    assert.equal(valueFor(atZoom(3), 3), 0.95);
    assert.equal(valueFor(atZoom(3), 4), 0);
    // End of the first fade window: grids have swapped.
    assert.equal(valueFor(atZoom(3.9), 3), 0);
    assert.equal(valueFor(atZoom(3.9), 4), 0.95);
    // z7: the res-5 overlay starts invisible and fades in over the res-4 base,
    // which never fades out (it backs the overlay outside the detail zone).
    assert.equal(valueFor(atZoom(7), 5), 0);
    assert.equal(valueFor(atZoom(7), 4), 0.95);
    assert.equal(valueFor(atZoom(7.9), 5), 0.95);
    assert.equal(valueFor(atZoom(7.9), 4), 0.95);
    // Old archives without a res property keep the base opacity.
    assert.equal(valueFor(atZoom(3), 99), 0.95);
});

test("hex and border layers use the band fade", async () => {
    const { buildHexworldStyle } = await import("../out/hexworld/style.js");
    const faded = buildHexworldStyle({ archiveURL: "/x.pmtiles" });
    const layer = (id) => faded.layers.find((l) => l.id === id);
    assert.equal(layer("hexworld-hex").paint["fill-opacity"][0], "interpolate");
    assert.equal(layer("hexworld-hex-outline").paint["line-opacity"][0], "interpolate");
    assert.equal(layer("hexworld-borders").paint["line-opacity"][0], "interpolate");
    assert.equal(layer("hexworld-region-borders").paint["line-opacity"][0], "interpolate");
});

test("label layers sort collisions by population and regions start at z3", async () => {
    const { buildHexworldStyle } = await import("../out/hexworld/style.js");
    const style = buildHexworldStyle({ archiveURL: "/x.pmtiles" });
    const region = style.layers.find((l) => l.id === "hexworld-label-region");
    assert.equal(region.minzoom, 3);
    for (const kind of ["country", "region", "locality"]) {
        const layer = style.layers.find((l) => l.id === `hexworld-label-${kind}`);
        const sort = layer.layout["symbol-sort-key"];
        assert.ok(Array.isArray(sort), `${kind} needs a symbol-sort-key`);
    }
});
